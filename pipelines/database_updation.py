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
import json

nest_asyncio.apply()

client = ApifyClient(APIFY_API_TOKEN)
client_async = ApifyClientAsync(APIFY_API_TOKEN)

# ---------------- GOOGLE DRIVE CONFIG ----------------

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH = "token.pickle"


# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------

def safe_str(v): return str(v).strip() if v else ""
def safe_int(v):
    try: return int(v)
    except: return 0

def clean_text(v):
    try:
        return str(v).encode("utf-8", "ignore").decode("utf-8")
    except:
        return ""

def flatten_list(lst):
    flat = []
    for i in lst:
        if isinstance(i, list): flat.extend(i)
        else: flat.append(i)
    return flat

def list_to_json(lst):
    return json.dumps(lst) if lst else "[]"

def extract_external_urls(ext):
    if isinstance(ext, list):
        return ", ".join([x.get("url", "") for x in ext if isinstance(x, dict)])
    return str(ext) if ext else ""

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
            return None, []

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

        # Airtable attachment format
        attachment = [{"url": drive_url}] if drive_url else []

        return drive_url, attachment

    except Exception as e:
        print(f"Profile pic upload error: {e}")
        return None, []


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


async def profile_scraper_database_updation(usernames: list):
    try:
        print("📡 Calling Apify actor...")

        run = await client_async.actor(
            "apify/instagram-profile-scraper"
        ).call(run_input={
            "usernames": usernames,
            "resultsType": "details"
        })

        dataset_id = run.get("defaultDatasetId")
        dataset_client = client_async.dataset(dataset_id)
        items = (await dataset_client.list_items()).items

        results = []

        for item in items:
            print("🔹 RAW ITEM:", item)

            username = safe_str(item.get("username"))
            followers = safe_int(item.get("followersCount"))

            profile_pic = (
                item.get("profilePicUrlHD")
                or item.get("profilePicUrl")
            )

            # 🔥 DOWNLOAD + UPLOAD
            drive_url, attachment = download_and_upload_profile_pic(profile_pic, username)

            data = {
                "instagram_url": safe_str(item.get("url") or item.get("inputUrl")),
                "instagram_username": username,
                "full_name": safe_str(item.get("fullName")),
                "instagram_bio": clean_text(item.get("biography")),
                "external_urls": extract_external_urls(item.get("externalUrls")),

                "instagram_profile_pic": safe_str(profile_pic),

                # ✅ NEW FIELDS
                "downloadable_profile_pic": drive_url,
                "saved_profile_pic": attachment,

                "instagram_followers_count": str(followers),
                "instagram_follows_count": str(safe_int(item.get("followsCount"))),
                "instagram_posts_count": str(safe_int(item.get("postsCount"))),
            }

            # POSTS
            posts = item.get("latestPosts", []) or []

            captions, hashtags, post_urls = [], [], []
            comments_counts, likes_counts, views, video_urls = [], [], [], []

            for post in posts:
                captions.append((post.get("caption") or "")[:80])
                hashtags.append(post.get("hashtags", []))
                post_urls.append(post.get("url", ""))

                comments_counts.append(safe_int(post.get("commentsCount")))
                likes_counts.append(safe_int(post.get("likesCount")))
                views.append(safe_int(post.get("videoViewCount")))
                video_urls.append(post.get("videoUrl", ""))

            hashtags = flatten_list(hashtags)

            avg_likes = int(sum(likes_counts)/len(likes_counts)) if likes_counts else 0
            avg_comments = int(sum(comments_counts)/len(comments_counts)) if comments_counts else 0
            avg_views = int(sum(views)/len(views)) if views else 0

            total_posts = len(likes_counts)

            total_engagement = sum(likes_counts) + sum(comments_counts)

            avg_engagement = total_engagement / total_posts if total_posts else 0

            engagement_rate = round((avg_engagement / followers) * 100, 2) if followers else 0

            
            # safety cap
            engagement_rate = min(engagement_rate, 100)

            # ✅ Engagement rate flag
            flag = ""
            if engagement_rate > 25:
                views_part = f"avg views {avg_views:,}, " if avg_views else ""
                flag = (
                    f"High engagement detected. "
                    f"Based on {total_posts} posts analysed, "
                    f"{followers:,} followers, "
                    f"avg likes {avg_likes:,}, "
                    f"avg comments {avg_comments:,}, "
                    f"{views_part}"
                    f"small sample — treat as directional."
                )


            data.update({
                "instagram_captions": clean_text(", ".join(captions))[:3000],
                "instagram_hashtags": clean_text(", ".join(hashtags))[:2000],
                "instagram_post_urls": clean_text(", ".join(post_urls))[:2000],

                "instagram_comments_counts": list_to_json(comments_counts),
                "instagram_likes_counts": list_to_json(likes_counts),
                "instagram_video_play_counts": list_to_json(views),
                "instagram_video_urls": list_to_json(video_urls),

                "avg_likes": str(avg_likes),
                "avg_comments": str(avg_comments),
                "avg_video_play_counts": str(avg_views),
                "engagement_rate": str(engagement_rate),
                "videos_engagement": str(avg_views),
                "engagement_rate_flag": flag 
                
            })

            print("📊 FINAL PROFILE DATA:", data)

            results.append(data)

        return results

    except Exception as e:
        print("❌ Scraper Error:", e)
        return []
