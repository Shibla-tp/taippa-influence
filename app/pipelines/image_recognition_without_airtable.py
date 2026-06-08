from flask import Flask, request, jsonify
import requests
import traceback
import os
import time
import pickle
import tempfile
import json
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, APIFY_API_TOKEN, OPENAI_API_KEY

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import openai
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

# === Google Drive Auth ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, 'credentials.json')
TOKEN_PATH = os.path.join(PROJECT_ROOT, 'token.pickle')
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_authenticated_drive_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)
    return build("drive", "v3", credentials=creds)

from io import BytesIO

def upload_to_drive(image_url):
    tmp_path = None
    try:
        response = requests.get(image_url, stream=True, timeout=30)
        if response.status_code != 200:
            print(f"⚠️ Failed to download image: {image_url}")
            return None

        # Save image to memory buffer
        buffer = BytesIO(response.content)

        # Write memory buffer to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg", mode='wb') as tmp_file:
            tmp_file.write(buffer.getvalue())
            tmp_path = tmp_file.name

        # Upload using MediaFileUpload
        drive_service = get_authenticated_drive_service()
        file_metadata = {"name": os.path.basename(tmp_path)}
        media = MediaFileUpload(tmp_path, mimetype="image/jpeg", resumable=False)

        uploaded = drive_service.files().create(
            body=file_metadata, media_body=media, fields="id"
        ).execute()
        file_id = uploaded.get('id')

        drive_service.permissions().create(
            fileId=file_id, body={"role": "reader", "type": "anyone"}
        ).execute()

        # Close file and delete after upload
        media._fd.close()  # 👈 Force close file descriptor before deletion
        os.remove(tmp_path)

        return f"https://drive.google.com/uc?id={file_id}&export=download"

    except Exception as e:
        print(f"❌ Error uploading to Drive: {e}")
        traceback.print_exc()
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as cleanup_err:
                print(f"⚠️ Cleanup error: {cleanup_err}")
        return None
def get_image_urls_from_apify(post_url):
    try:
        payload = {"url": post_url}
        headers = {'Content-Type': 'application/json'}
        run_response = requests.post(
            f"https://api.apify.com/v2/acts/pratikdani~instagram-posts-scraper/runs?token={APIFY_API_TOKEN}",
            json=payload,
            headers=headers
        )
        run_response.raise_for_status()
        run_data = run_response.json()
        run_id = run_data.get("data", {}).get("id")
        if not run_id:
            return []

        # Wait for Apify to complete scraping
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_API_TOKEN}"
        max_wait_time, poll_interval, elapsed = 60, 5, 0
        while elapsed < max_wait_time:
            status_response = requests.get(status_url)
            status_data = status_response.json().get("data", {})
            status = status_data.get("status")
            if status == "SUCCEEDED":
                dataset_id = status_data.get("defaultDatasetId")
                break
            elif status in {"FAILED", "TIMED-OUT", "ABORTED"}:
                return []
            time.sleep(poll_interval)
            elapsed += poll_interval
        else:
            return []

        # Fetch result
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_API_TOKEN}"
        items = requests.get(dataset_url).json()

        if not items or not isinstance(items, list):
            return []

        item = items[0]

        # Return photo
        if item.get("photos"):
            return [item["photos"][0]]

        # Return video thumbnail
        if item.get("videos") and item.get("thumbnail"):
            return [item["thumbnail"]]

        # Fallback to post_content logic
        post_content = item.get("post_content", [])
        for media in post_content:
            if media.get("type") == "Photo" and media.get("url"):
                return [media["url"]]
            elif media.get("type") == "Video" and item.get("thumbnail"):
                return [item["thumbnail"]]

        return []

    except Exception as e:
        print("❌ Error in get_image_urls_from_apify:")
        traceback.print_exc()
        return []

def analyze_image_with_gpt(image_url):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """
Analyze the image and generate image tags for the given image. Return ONLY a JSON object like:
{"tags": ["coffee", "beach", "phone"]}
Rules:
- Include actions, objects, clothing, and locations useful for influencer marketing.
- No explanation. Just the JSON.
                            """
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            max_tokens=200,
            temperature=0.5,
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        traceback.print_exc()
        return {"tags": []}  
    
def image_analysis_endpoint(data):
    try:
        post_urls = data.get("post_urls", [])

        if not isinstance(post_urls, list) or not post_urls:
            return jsonify({"error": "Invalid or missing 'post_urls'"}), 400

        results = []
        all_post_urls = []
        all_image_urls = []
        all_drive_urls = []
        all_tags = []

        for post_url in post_urls:
            result = {"post_url": post_url}
            image_urls = get_image_urls_from_apify(post_url)
            if not image_urls:
                result["status"] = "failed"
                result["reason"] = "No image found"
                results.append(result)
                continue

            image_url = image_urls[0]
            drive_url = upload_to_drive(image_url)
            if not drive_url:
                result["status"] = "failed"
                result["reason"] = "Drive upload failed"
                results.append(result)
                continue

            tags_data = analyze_image_with_gpt(drive_url)
            tags = tags_data.get("tags", [])

            result.update({
                "image_url": image_url,
                "drive_url": drive_url,
                "tags": tags,
                "status": "success"
            })
            results.append(result)

            # ✅ Aggregate values
            all_post_urls.append(post_url)
            all_image_urls.append(image_url)
            all_drive_urls.append(drive_url)
            all_tags.extend(tags)

        return jsonify({
            "results": results,
            "all_post_urls": all_post_urls,
            "all_image_urls": all_image_urls,
            "all_drive_urls": all_drive_urls,
            "all_tags": list(set(all_tags)) 
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
