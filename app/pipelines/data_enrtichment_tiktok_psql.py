from flask import Flask, request, jsonify
import requests
import json
import traceback
from config import APIFY_API_TOKEN
from db.db_ops import db_manager 

# Apify Clockworks Scraper
CLOCKWORKS_URL = f"https://api.apify.com/v2/acts/clockworks~tiktok-profile-scraper/run-sync-get-dataset-items?token={APIFY_API_TOKEN}"

app = Flask(__name__)

def scrape_and_store_psql(username):
    try:
        payload = {
            "profiles": [username],
            "resultsPerPage": 5,
            "shouldDownloadCovers": False,
            "shouldDownloadSlideshowImages": False,
            "shouldDownloadSubtitles": False,
            "shouldDownloadVideos": False
        }

        table_name = "src_influencer_data_demo"
        print("📡 Payload sent to Apify:", payload)

        response = requests.post(CLOCKWORKS_URL, json=payload)
        if response.status_code not in (200, 201):
            return {"status": "failed", "error": f"Apify error: {response.text}"}

        posts = response.json()
        print("📦 Number of posts received:", len(posts))

        if not posts or not isinstance(posts, list):
            return {"status": "failed", "error": "No posts returned or data not a list"}

        recent_posts = posts[:5]

        

        # Check if username exists
        cols_list = ["tiktok_username"]
        col_values = [username]
        existing = db_manager.get_records_with_filter(table_name, cols_list, col_values, limit=1)
        
        if existing is None:
            print("⚠️ No result returned from db_manager (possible DB error)")
            return {"status": "failed", "error": "Database connection issue or no result returned"}
        print(f"🔍 Matching record found: {existing}")
        print(f"🔍 Matching record found: {len(existing)}")
        data = {
            "id": existing["id"],
            "tiktok_username": username,
            "tiktok_share_count": json.dumps([p.get('shareCount', 0) for p in recent_posts]),
            "tiktok_play_count": json.dumps([p.get('playCount', 0) for p in recent_posts]),
            "tiktok_comment_count": json.dumps([p.get('commentCount', 0) for p in recent_posts]),
            "tiktok_digg_count": json.dumps([p.get('diggCount', 0) for p in recent_posts]),
            "tiktok_text": json.dumps([p.get('text', '') for p in recent_posts]),
            "tiktok_video_urls": json.dumps([p.get('webVideoUrl', '') for p in recent_posts])
        }

        if existing:
            # record_id = existing["id"]
            # print(f"Primary key:{record_id}")
            record = db_manager.update_multiple_fields(table_name, data, "id")
            action = "updated"
        else:
            record = db_manager.insert_data(table_name, data)
            action = "created"

        print(f"✅ PostgreSQL {action} response for {username}:", record, flush=True)

        return {
            "status": "passed",
            "message": f"TikTok posts data {action} successfully",
            "data": data
        }

    except Exception as e:
        print(f"❌ Unexpected error for {username}:", e, flush=True)
        traceback.print_exc()
        return {"status": "failed", "error": f"Unexpected error: {str(e)}"}

if __name__ == '__main__':
    app.run(debug=True)
