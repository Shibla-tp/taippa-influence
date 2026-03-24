# -------------------- database_updation.py --------------------

import os
import pickle
import asyncio
import tempfile
import requests
import nest_asyncio
from apify_client import ApifyClient, ApifyClientAsync
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from config import APIFY_API_TOKEN

nest_asyncio.apply()

client = ApifyClient(APIFY_API_TOKEN)
client_async = ApifyClientAsync(APIFY_API_TOKEN)

# ---------------- GOOGLE DRIVE CONFIG ----------------

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH = "token.pickle"


# =====================================================
# GOOGLE DRIVE AUTH
# =====================================================

def get_authenticated_drive_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)


# =====================================================
# GENERIC DRIVE UPLOAD
# =====================================================

def upload_file_to_drive(file_path, filename, mime_type):
    drive_service = get_authenticated_drive_service()

    file_metadata = {"name": filename}
    media = MediaFileUpload(file_path, mimetype=mime_type)

    uploaded = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    file_id = uploaded.get("id")

    drive_service.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"}
    ).execute()

    return f"https://drive.google.com/uc?id={file_id}&export=download"


# =====================================================
# PROFILE PIC UPLOAD
# =====================================================

def download_and_upload_profile_pic(profile_pic_url, username):
    try:
        response = requests.get(profile_pic_url, stream=True, timeout=60)
        if response.status_code != 200:
            return None

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            for chunk in response.iter_content(1024):
                tmp.write(chunk)
            tmp_path = tmp.name

        filename = f"{username}_profile_pic.jpg"

        drive_url = upload_file_to_drive(
            tmp_path,
            filename,
            "image/jpeg"
        )

        os.remove(tmp_path)
        return drive_url

    except Exception as e:
        print(f"Profile pic upload error: {e}")
        return None


# =====================================================
# POST MEDIA UPLOAD
# =====================================================

def download_and_upload_post_media(media_url, username, index):
    try:
        response = requests.get(media_url, stream=True, timeout=60)
        if response.status_code != 200:
            return None

        if ".mp4" in media_url:
            suffix = ".mp4"
            mime_type = "video/mp4"
        else:
            suffix = ".jpg"
            mime_type = "image/jpeg"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in response.iter_content(1024):
                tmp.write(chunk)
            tmp_path = tmp.name

        filename = f"{username}_post_{index}{suffix}"

        drive_url = upload_file_to_drive(tmp_path, filename, mime_type)

        os.remove(tmp_path)
        return drive_url

    except Exception as e:
        print(f"Post upload error: {e}")
        return None


# =====================================================
# PROFILE SCRAPER
# =====================================================

def profile_scraper(username):
    try:
        input_object = {"usernames": [username]}

        async def run():
            return await client_async.actor(
                "apify/instagram-profile-scraper"
            ).call(run_input=input_object)

        result = asyncio.get_event_loop().run_until_complete(run())
        dataset = client.dataset(result["defaultDatasetId"])
        items = dataset.list_items().items

        if not items:
            return {}

        item = items[0]

        return {
            "instagram_bio": item.get("biography"),
            "instagram_profile_pic": item.get("profilePicUrl"),
            "instagram_followers_count": item.get("followersCount"),
            "instagram_follows_count": item.get("followsCount"),
            "instagram_posts_count": item.get("postsCount")
        }

    except Exception as e:
        print(f"Profile scraper error: {e}")
        return {}


# =====================================================
# POST SCRAPER
# =====================================================

def post_scraper(username, posts_count=5):
    try:
        input_object = {
            "resultsLimit": posts_count,
            "username": [username]
        }

        async def run():
            return await client_async.actor(
                "apify/instagram-post-scraper"
            ).call(run_input=input_object)

        result = asyncio.get_event_loop().run_until_complete(run())
        dataset = client.dataset(result["defaultDatasetId"])
        items = dataset.list_items().items

        media_urls = []
        likes = []
        comments = []
        views = []

        for item in items:
            media_url = (
                item.get("videoUrl")
                or item.get("displayUrl")
                or item.get("imageUrl")
            )

            if media_url:
                media_urls.append(media_url)

            likes.append(item.get("likesCount", 0))
            comments.append(item.get("commentsCount", 0))
            views.append(item.get("videoViewCount", 0))

        return {
            "instagram_video_urls": str(media_urls),
            "instagram_likes_counts": str(likes),
            "instagram_comments_counts": str(comments),
            "instagram_video_play_counts": str(views),
            "avg_likes": sum(likes)/len(likes) if likes else 0,
            "avg_comments": sum(comments)/len(comments) if comments else 0,
            "avg_video_play_counts": sum(views)/len(views) if views else 0
        }

    except Exception as e:
        print(f"Post scraper error: {e}")
        return {}
