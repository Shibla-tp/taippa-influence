from flask import Flask, request, jsonify
from openai import OpenAI
import json
import re
from db.db_ops import db_manager
from config import OPENAI_API_KEY

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)

# === Utility ===
def clean_json_block(raw_text):
    """Remove triple backtick code blocks if GPT wraps response."""
    clean = re.sub(r"^```(?:json)?\n?", "", raw_text.strip())
    clean = re.sub(r"\n?```$", "", clean)
    return clean.strip()

# === GPT Function 1: Profile Enrichment ===
def tiktok_enritchment(tiktok_bio, tiktok_text, tiktok_username):
    function_schema = {
        "name": "analyze_tiktok_profile",
        "description": "Analyze TikTok profile and return structured enrichment data",
        "parameters": {
            "type": "object",
            "properties": {
                "niche": {"type": "string"},
                "languages_used": {"type": "array", "items": {"type": "string"}},
                "content_type": {"type": "string"},
                "audience_location": {"type": "string"},
                "content_style": {"type": "string"},
                "suitable_brands": {"type": "array", "items": {"type": "string"}},
                "summary": {"type": "string"},
                "instagram_url": {"type": "string"},
                "twitter_url": {"type": "string"},
                "snapchat_url": {"type": "string"},
                "linkedin_url": {"type": "string"},
                "youtube_url": {"type": "string"},
                "influencer_nationality": {"type": "string"},
                "targeted_domain": {"type": "string"},
                "full_name": {"type": "string"},
                
            },
            "required": ["niche", "languages_used", "content_type", "audience_location", "content_style", "suitable_brands", "summary", "instagram_url", "twitter_url", "snapchat_url", "linkedin_url", "youtube_url", "influencer_nationality", "targeted_domain", "full_name"]
        }
    }

    prompt = f"""
Analyze the following TikTok profile:

Username: {tiktok_username}
Bio: {tiktok_bio}
Posts: {tiktok_text}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            functions=[function_schema],
            function_call={"name": "analyze_tiktok_profile"},
            temperature=0.7
        )
        message = response.choices[0].message
        if not message.function_call or not message.function_call.arguments:
            return None
        enriched_data = json.loads(message.function_call.arguments)
        return enriched_data
    except Exception as e:
        print("❌ GPT enrichment failed:", e)
        return None

# === GPT Function 2: Contact & Audience ===
def tiktok_extract_contact_and_audience(tiktok_bio, tiktok_text, tiktok_username):
    prompt = f"""
Analyze the following social media profile data and extract:

1. Any email addresses mentioned (visible in bio or captions)
2. Any phone numbers mentioned (in international or local format)
3. The most likely target audience: "gen-x", "gen-y", or "gen-z"
4. Any instagram url addresses mentioned (visible in bio or captions)

Focus only on these three values and return your response in **this exact JSON format** (with double quotes only, no explanation):

{{
  "email": "",
  "phone": "",
  "target_audience": "",
  
}}

Input:
- Username: {tiktok_username}
- Bio: {tiktok_bio}
- Posts: {tiktok_text}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        raw_response = response.choices[0].message.content.strip()
        print(f"🔎 Raw GPT JSON string:\n{raw_response}\n")

        cleaned = clean_json_block(raw_response)
        return json.loads(cleaned)

    except Exception as e:
        print("❌ Contact extraction failed:", e)
        return None
# === GPT Function 3: Identity Detection (Person/Group/Nationality/Instagram) ===
def tiktok_identity_analysis(tiktok_bio, tiktok_text, tiktok_username):
    prompt = f"""
You are a smart assistant programmed to analyze TikTok influencer data and determine whether the profile belongs to an individual person or a group/team.

Extract the following:
- Full Instagram URL if found in bio or posts
- "profile_type": either "person" or "group"
- "influencer_nationality": best guess from context; if unknown, return "unknown"

Format:
{{
  "profile_type": "person",
  "influencer_nationality": "Emirati",
  "instagram_url": "https://instagram.com/example"
}}

Input:
- Username: {tiktok_username}
- Bio: {tiktok_bio}
- Posts: {tiktok_text}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        raw = clean_json_block(response.choices[0].message.content)
        return json.loads(raw)
    except Exception as e:
        print("❌ Identity analysis failed:", e)
        return None

# === Core Logic ===
def data_entrichment_using_gpt(username):
    table_name = "src_influencer_data_demo"
    cols_list = ["tiktok_username"]
    col_values = [username]

    result = db_manager.get_records_with_filter(table_name, cols_list, col_values, limit=1)
    if not result:
        return {"status": "failed", "message": f"No record found for {username}"}

    # result is a dict (not list)
    record = result if isinstance(result, dict) else result[0]

    print(f"✅ Record: {record}", flush=True)

    tiktok_bio = record.get("tiktok_bio", "")
    tiktok_text = record.get("tiktok_text", "")
    tiktok_username = record.get("tiktok_username", "")

    enriched = tiktok_enritchment(tiktok_bio, tiktok_text, tiktok_username)
    contact_info = tiktok_extract_contact_and_audience(tiktok_bio, tiktok_text, tiktok_username)
    identity_info = tiktok_identity_analysis(tiktok_bio, tiktok_text, tiktok_username)

    if enriched is None and contact_info is None and identity_info is None:
        return {"status": "failed", "message": "GPT enrichment failed"}
    print(f"Enriched Data:{enriched}")
    data = {
            "id": result["id"],
            "tiktok_username": username,
            "tiktok_niche": enriched.get("niche", "N/A") if enriched else "N/A",
            "tiktok_language_used": ", ".join(enriched.get("languages_used", [])) if enriched and enriched.get("languages_used") else "N/A",
            "tiktok_content_type": enriched.get("content_type", "N/A") if enriched else "N/A",
            "tiktok_content_style": enriched.get("content_style", "N/A") if enriched else "N/A",
            "tiktok_audience_location": enriched.get("audience_location", "N/A") if enriched else "N/A",
            "tiktok_suitable_brands": ", ".join(enriched.get("suitable_brands", [])) if enriched and enriched.get("suitable_brands") else "N/A",
            "tiktok_influencer_summary": enriched.get("summary", "N/A") if enriched else "N/A",            
            "twitter_url": enriched.get("twitter_url", "N/A") if enriched else "N/A",
            "snapchat_url": enriched.get("snapchat_url", "N/A") if enriched else "N/A",
            # "youtube_url":enriched.get("youtube_url", "N/A") if enriched else "N/A",
            "targeted_domain" : enriched.get("targeted_domain", "N/A") if enriched else "N/A",
            # "email": contact_info.get("email", "N/A") if contact_info else "N/A",
            "email_id": contact_info.get("email", "N/A") if contact_info else "N/A",
            "phone": contact_info.get("phone", "N/A") if contact_info else "N/A",
            "targeted_audience": contact_info.get("targeted_audience", "N/A") if contact_info else "N/A",            
            "instagram_url": identity_info.get("instagram_url", "N/A") if identity_info else enriched.get("instagram_url", "N/A"),
            "influencer_nationality": identity_info.get("influencer_nationality", "N/A") if identity_info else enriched.get("influencer_nationality", "N/A"),
            "profile_type": identity_info.get("profile_type", "N/A") if identity_info else "N/A",
            "linkedin_url": enriched.get("linkedin_url", "N/A")if enriched else "N/A",
            "full_name": enriched.get("full_name", "N/A") if enriched else "N/A",
        }

    db_manager.update_multiple_fields(table_name, data, "id")
    print(f"⚠️ No existing record found with Instagram URL. Updating current record.")

    instagram_url = enriched["instagram_url"]
    print(f"Instagram Url:{instagram_url}")
    
    if instagram_url:
        cols_list = ["instagram_url"]
        col_values = [instagram_url]
        existing = db_manager.get_records_with_filter("influencers", cols_list, col_values, limit=1)

    if existing:
        existing_record = existing if isinstance(existing, dict) else existing[0]
        data = {
            "id": existing_record["id"],
            "full_name": enriched.get("full_name", "N/A") if enriched else "N/A",
            "email_id": contact_info.get("email", "N/A") if contact_info else "N/A",
            "phone": contact_info.get("phone", "N/A") if contact_info else result.get("phone", "N/A"),
            "tiktok_url": result.get("tiktok_url", "N/A"),
            
        }

        db_manager.update_multiple_fields("influencers", data, "id")
        print(f"✅ Updated Influencers table existing record with matching Instagram URL.")
    else:
        data = {
            "id": result["id"],
            "full_name": enriched.get("full_name", "N/A") if enriched else "N/A",
            "email_id": contact_info.get("email", "N/A") if contact_info else "N/A",
            "phone": contact_info.get("phone", "N/A") if contact_info else result.get("phone", "N/A"),
            "tiktok_url": result.get("tiktok_url", "N/A"),          
            "instagram_url": identity_info.get("instagram_url", "N/A") if identity_info else enriched.get("instagram_url", "N/A"),
        }

        db_manager.update_multiple_fields(table_name, data, "id")
        print(f"⚠️ No existing record found with Instagram URL. Updating current record.")


    return {
        "status": "success",
        "username": username,
        "enriched_data": enriched,
        "contact_audience_data": contact_info,
        "identity_info": identity_info
    }

# # === API Endpoint ===
# @app.route("/data_entrichment_using_gpt_psql", methods=["GET"])
# def data_entrichment_using_gpt_psql():
#     try:
#         username = request.args.get("username")
#         if not username:
#             return jsonify({"status": "failed", "content": "Missing 'username' parameter"})

#         result = data_entrichment_using_gpt(username)
#         if result["status"] == "failed":
#             return jsonify({"status": "failed", "content": result.get("message", "Unknown error")})

#         return jsonify({"status": "passed", "content": result})

#     except Exception as e:
#         print(f"❌ Error occurred: {e}")
#         return jsonify({"status": "failed", "content": "Internal server error"})

if __name__ == "__main__":
    app.run(debug=True)
