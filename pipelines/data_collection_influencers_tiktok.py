from flask import Flask, request, jsonify
import requests
import json
import traceback
from config import APIFY_API_TOKEN

app = Flask(__name__)

ACTOR_RUN_URL = (
    f"https://api.apify.com/v2/acts/direct_houseboat~tiktok-user-profile-scraper/"
    f"run-sync-get-dataset-items?token={APIFY_API_TOKEN}"
)

@app.route('/scrape_tiktok_profile', methods=['GET'])
def scrape_tiktok_profile_endpoint():
    try:
        tiktok_username = request.args.get("username")
        if not tiktok_username:
            return jsonify({"status": "failed", "content": "Missing 'username' parameter"})

        result = scrape_tiktok_profile(tiktok_username)
        if result["status"] == "failed":
            return jsonify({"status": "failed", "content": result.get("error", "Unknown error")})

        return jsonify({"status": "passed", "content": result})

    except Exception as e:
        print(f"Error occurred: {e}")
        traceback.print_exc()
        return jsonify({"status": "failed", "content": "Error occurred"})


def scrape_tiktok_profile(username):
    try:
        payload = {
            "usernames": [username]
        }

        response = requests.post(ACTOR_RUN_URL, json=payload)
        print("📡 Apify HTTP status:", response.status_code)
        print("📡 Apify raw response:", response.text)

        if response.status_code not in (200, 201):
            return {"status": "failed", "error": f"Failed to run actor: {response.text}"}

        resp_json = response.json()

        data = None
        if isinstance(resp_json, list):
            data = resp_json
        elif "error" in resp_json and isinstance(resp_json["error"], str):
            try:
                data = json.loads(resp_json["error"])
            except Exception as e:
                return {"status": "failed", "error": f"Failed to parse nested error JSON: {str(e)}"}
        elif "data" in resp_json and isinstance(resp_json["data"], list):
            data = resp_json["data"]

        if not data or not isinstance(data, list):
            return {"status": "failed", "error": f"No data returned or not a list: {data}"}

        profile = data[0]

        output_data = {
            "tiktok_username": profile.get("username", ""),
            "tiktok_followers_count": profile.get("total_followers", ""),
            "tiktok_follows_count": profile.get("total_followings", ""),
            "tiktok_likes_count": profile.get("likes", ""),
            "tiktok_videos_count": profile.get("total_videos", ""),
            "tiktok_bio": profile.get("bio", ""),
            "tiktok_url": profile.get("external_link", ""),
            "tiktok_profile_pic": profile.get("profile_picture", ""),
            "email_id": profile.get("email", ""),
            "phone": profile.get("phone", ""),
            "full_name": profile.get("fullName", ""),
            "external_urls": profile.get("external_link", ""),
            "profile_type": "tiktok",
            "influencer_type": "tiktok",
            "influencer_nationality": "",
            "influencer_location": "",
            "targeted_audience": "",
            "targeted_domain": ""
        }

        return {"status": "passed", "data": output_data}

    except Exception as e:
        traceback.print_exc()
        return {"status": "failed", "error": f"Unexpected error: {str(e)}"}


if __name__ == '__main__':
    app.run(debug=True)
