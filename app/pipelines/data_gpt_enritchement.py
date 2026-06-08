from flask import Flask, request, jsonify
from openai import OpenAI
from config import OPENAI_API_KEY
import json
import re

app = Flask(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

# === Utility ===
def clean_json_block(raw_text):
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
            "required": [
                "niche", "languages_used", "content_type", "audience_location",
                "content_style", "suitable_brands", "summary", "instagram_url",
                "twitter_url", "snapchat_url", "linkedin_url", "youtube_url",
                "influencer_nationality", "targeted_domain", "full_name"
            ]
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
        return json.loads(message.function_call.arguments)
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

Return this exact JSON format:

{{
  "email": "",
  "phone": "",
  "target_audience": ""
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
        print("❌ Contact extraction failed:", e)
        return None


# === GPT Function 3: Identity Analysis ===
def tiktok_identity_analysis(tiktok_bio, tiktok_text, tiktok_username):
    prompt = f"""
You are a smart assistant programmed to analyze TikTok influencer data and determine:

- "profile_type": either "person" or "group"
- "influencer_nationality": best guess from context; if unknown, return "unknown"
- Full Instagram URL if mentioned in bio or posts

Return this format:

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


# === Main Logic ===
def data_entrichment_using_gpt_airtable(data_dict):
    print(f"✅ Received Dict: {data_dict}")

    
def safe_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

def data_entrichment_using_gpt_airtable(data_dict):
    print(f"✅ Received Dict: {data_dict}")

    # Parse TikTok bio/text
    tiktok_bio = data_dict.get("tiktok_bio", "")
    tiktok_text = data_dict.get("tiktok_text", "")
    tiktok_username = data_dict.get("tiktok_username", "")

    # Extract numeric engagement fields
    likes = safe_int(data_dict.get("tiktok_digg_count"))
    comments = safe_int(data_dict.get("tiktok_comment_count"))
    shares = safe_int(data_dict.get("tiktok_share_count"))
    followers = safe_int(data_dict.get("tiktok_followers_count"))
    play_count = safe_int(data_dict.get("tiktok_play_count"))
    videos_count = safe_int(data_dict.get("tiktok_videos_count"))

    total_engagements = likes + comments + shares
    engagement_rate = round((total_engagements / followers) * 100, 2) if followers > 0 else 0
    estimated_reach = play_count

    enriched = tiktok_enritchment(tiktok_bio, tiktok_text, tiktok_username)
    contact_info = tiktok_extract_contact_and_audience(tiktok_bio, tiktok_text, tiktok_username)
    identity_info = tiktok_identity_analysis(tiktok_bio, tiktok_text, tiktok_username)

    if enriched is None and contact_info is None and identity_info is None:
        return {"status": "failed", "message": "GPT enrichment failed"}

    data = {
        "tiktok_username": tiktok_username,
        "tiktok_niche": enriched.get("niche", "N/A") if enriched else "N/A",
        "tiktok_language_used": ", ".join(enriched.get("languages_used", [])) if enriched else "N/A",
        "tiktok_content_type": enriched.get("content_type", "N/A") if enriched else "N/A",
        "tiktok_content_style": enriched.get("content_style", "N/A") if enriched else "N/A",
        "tiktok_audience_location": enriched.get("audience_location", "N/A") if enriched else "N/A",
        "tiktok_suitable_brands": ", ".join(enriched.get("suitable_brands", [])) if enriched else "N/A",
        "tiktok_influencer_summary": enriched.get("summary", "N/A") if enriched else "N/A",
        "instagram_url": identity_info.get("instagram_url", "N/A") if identity_info else enriched.get("instagram_url", "N/A"),
        "influencer_nationality": identity_info.get("influencer_nationality", "N/A") if identity_info else enriched.get("influencer_nationality", "N/A"),
        "profile_type": identity_info.get("profile_type", "N/A") if identity_info else "N/A",
        "email_id": contact_info.get("email", "N/A") if contact_info else "N/A",
        "phone": contact_info.get("phone", "N/A") if contact_info else "N/A",
        "targeted_audience": contact_info.get("targeted_audience", "N/A") if contact_info else "N/A",
        "linkedin_url": enriched.get("linkedin_url", "N/A") if enriched else "N/A",
        "twitter_url": enriched.get("twitter_url", "N/A") if enriched else "N/A",
        "snapchat_url": enriched.get("snapchat_url", "N/A") if enriched else "N/A",
        "targeted_domain": enriched.get("targeted_domain", "N/A") if enriched else "N/A",
        "full_name": enriched.get("full_name", "N/A") if enriched else "N/A",
        "engagement_rate": f"{engagement_rate}%",
        "estimated_engagement_count": str(total_engagements),
        "estimated_reach": str(estimated_reach)
    }

    return {
        "status": "success",
        "username": tiktok_username,
        "enriched_data": enriched,
        "contact_audience_data": contact_info,
        "identity_info": identity_info,
        "combined_output": data
    }


if __name__ == "__main__":
    app.run(debug=True)
