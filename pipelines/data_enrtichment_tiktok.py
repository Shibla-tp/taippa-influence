from flask import Flask, request, jsonify
import requests
import json
import traceback
from config import APIFY_API_TOKEN

app = Flask(__name__)

# Apify Clockworks Scraper URL
CLOCKWORKS_URL = "https://api.apify.com/v2/acts/clockworks~tiktok-profile-scraper/run-sync-get-dataset-items"
CLOCKWORKS_URL += f"?token={APIFY_API_TOKEN}"




def scrape_and_store(username):
    try:
        payload = {
            "profiles": [username],
            "resultsPerPage": 5,
            "shouldDownloadCovers": False,
            "shouldDownloadSlideshowImages": False,
            "shouldDownloadSubtitles": False,
            "shouldDownloadVideos": False
        }

        print("📡 Sending to Apify:", payload)
        response = requests.post(CLOCKWORKS_URL, json=payload)

        if response.status_code not in (200, 201):
            return {"status": "failed", "error": f"Apify error: {response.text}"}

        posts = response.json()

        if not posts or not isinstance(posts, list):
            return {"status": "failed", "error": "No posts returned or invalid format"}

        recent_posts = posts[:5]

        output_data = {
            "tiktok_username": username,
            "tiktok_share_count": [p.get("shareCount", 0) for p in recent_posts],
            "tiktok_play_count": [p.get("playCount", 0) for p in recent_posts],
            "tiktok_comment_count": [p.get("commentCount", 0) for p in recent_posts],
            "tiktok_digg_count": [p.get("diggCount", 0) for p in recent_posts],
            "tiktok_text": [p.get("text", "") for p in recent_posts],
            "tiktok_video_urls": [p.get("webVideoUrl", "") for p in recent_posts]
        }

        print("✅ Final JSON output:", json.dumps(output_data, indent=2))
        return {"status": "passed", "data": output_data}

    except Exception as e:
        print(f"❌ Error occurred for {username}:", e)
        traceback.print_exc()
        return {"status": "failed", "error": f"Unexpected error: {str(e)}"}


if __name__ == '__main__':
    app.run(debug=True)
