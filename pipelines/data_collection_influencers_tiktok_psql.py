from flask import Flask, request, jsonify
import requests
from db.db_ops import db_manager 
from config import APIFY_API_TOKEN
import json
import traceback
# Configurations
# APIFY_API_TOKEN = "apify_api_M6WCO92denEYVsZHPSKXTq8X5rZ73r187vDN"
ACTOR_RUN_URL = f"https://api.apify.com/v2/acts/direct_houseboat~tiktok-user-profile-scraper/run-sync-get-dataset-items?token={APIFY_API_TOKEN}"
app = Flask(__name__) 

@app.route('/scrape_tiktok_profile_psql', methods=['GET'])
def scrape_tiktok_profile_endpoint_psql():
    try:
        tiktok_username = request.args.get("username")
        if not tiktok_username:
            return jsonify({"status": "failed", "content": "Missing 'username' parameter"})
        result = scrape_tiktok_profile_psql(tiktok_username)
        if result["status"] == "failed":
            return jsonify({"status": "failed", "content": result.get("error", "Unknown error")})
        return jsonify({"status": "passed", "content": result})
    except Exception as e:
        print(f"Error occurred : {e}")
        return jsonify({"status": "failed", "content": "Error occurred"})

def scrape_tiktok_profile_psql(username):
    try:
        # Call Apify Actor with username
        payload = {
            "usernames": [username]
        }

        response = requests.post(ACTOR_RUN_URL, json=payload)
        print("Apify HTTP status:", response.status_code, flush=True)
        print("Apify raw response:", response.text, flush=True)
        table_name = "src_influencer_data_demo"
        if response.status_code not in (200, 201):
            return {"status": "failed", "error": f"Failed to run actor: {response.text}"}

        resp_json = response.json()
        print("Apify response JSON:", resp_json, flush=True)

        data = None

        # Check if Apify returned a list directly
        if isinstance(resp_json, list):
            data = resp_json
        # Check if Apify returned a stringified list in the "error" field
        elif "error" in resp_json and isinstance(resp_json["error"], str):
            try:
                data = json.loads(resp_json["error"])
                print("Parsed data from 'error' field:", data, flush=True)
            except Exception as e:
                print("Failed to parse nested error JSON:", e, flush=True)
                traceback.print_exc()
                return {"status": "failed", "error": f"Failed to parse nested error JSON: {str(e)}"}
        # Check if Apify returned a list in the "data" field
        elif "data" in resp_json and isinstance(resp_json["data"], list):
            data = resp_json["data"]

        print("Parsed data:", data, flush=True)

        if not data or not isinstance(data, list):
            return {"status": "failed", "error": f"No data returned or data not a list: {data}"}

        profile = data[0]  # This is your TikTok profile dict
        print("Profile to insert:", profile, flush=True)

        data = {
            "tiktok_username": str(profile.get("username", "")),
            "tiktok_followers_count": str(profile.get("total_followers", "")),
            "tiktok_follows_count": str(profile.get("total_followings", "")),
            "tiktok_likes_count": str(profile.get("likes", "")),
            "tiktok_videos_count": str(profile.get("total_videos", "")),
            "tiktok_bio": str(profile.get("bio", "")),
            "tiktok_url": str(profile.get("external_link", "")),
            "tiktok_profile_pic": str(profile.get("profile_picture", "")),
            "email_id": str(profile.get("email", "")),
            "phone": str(profile.get("phone", "")),
            "full_name": str(profile.get("fullName", "")),
            "instagram_username": "",
            "instagram_followers_count": "",
            "linkedin_url": "",
            "twitter_url": "",
            "snapchat_url": "",
            "external_urls": str(profile.get("external_link", "")),
            "profile_type": "tiktok",
            "influencer_type": "tiktok",
            "influencer_nationality": "",
            "influencer_location": "",
            "targeted_audience": "",
            "targeted_domain": ""            
        }
        

        print("Prepared PSQL data:", data, flush=True)
        cols_list = ["tiktok_username"]
        col_values = [username]
        existing = db_manager.get_records_with_filter(table_name, cols_list, col_values, limit=1)
        # # Upsert logic: update if exists, else create
        # existing_records = 
        # if existing_records:
        #     record_id = existing_records[0]['id']
        #     record = airtable.update(record_id, airtable_data)
        #     action = "updated"
        # else:
        #     record = airtable.create(airtable_data)
        #     action = "created"

        # print(f"Airtable {action} response for {username}:", record, flush=True)
        if not existing:
            db_manager.insert_data("src_influencer_data_demo", data)
        else:
            print(f"{username} already exist in {table_name}")
        return {"status": "passed", "message": f"Profile data added successfully", "data": data}

    except Exception as e:
        print("Unexpected error:", e, flush=True)
        traceback.print_exc()
        return {"status": "failed", "error": f"Unexpected error: {str(e)}"}



if __name__ == '__main__':
    app.run(debug=True)