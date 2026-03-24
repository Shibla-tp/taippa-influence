import os
import asyncio
from pyairtable import Table
from apify_client import ApifyClientAsync, ApifyClient
from flask import Flask, jsonify

app = Flask(__name__)

# -----------------------------------
# Config
# -----------------------------------
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

# Sync client for Airtable & Apify
apify_client = ApifyClient(APIFY_API_TOKEN)

# -----------------------------------
# Utility Functions
# -----------------------------------
def safe_int(val):
    try:
        return int(val)
    except:
        return 0

def only_text(val):
    if isinstance(val, list):
        return str(val[0]) if val else ""
    return str(val) if val is not None else ""

def calc_engagement_rate(likes, comments, views):
    """Calculate engagement rate %"""
    try:
        likes = safe_int(likes)
        comments = safe_int(comments)
        views = safe_int(views)
        if views == 0:
            return "0%"
        rate = ((likes + comments) / views) * 100
        return f"{rate:.2f}%"
    except:
        return "0%"

def parse_percentage_to_float(percentage_str):
    if not percentage_str:
        return 0.0
    s = str(percentage_str).strip()
    if s.endswith("%"):
        s = s[:-1]
    try:
        return float(s)
    except:
        return 0.0

def calc_engagement_rate(likes, comments, views_or_followers):
    """Calculate engagement rate %"""
    try:
        likes = safe_int(likes)
        comments = safe_int(comments)
        base = safe_int(views_or_followers)
        if base == 0:
            return "0%"
        rate = ((likes + comments) / base) * 100
        return f"{rate:.2f}%"
    except:
        return "0%"

# -----------------------------------
# Scraper for a single Instagram post
# -----------------------------------
def post_scraper(instagram_post_url):
    """Scrape single Instagram post using pratikdani/instagram-posts-scraper"""
    try:
        input_object = {"url": instagram_post_url}

        async def run_actor():
            client_async = ApifyClientAsync(APIFY_API_TOKEN)
            return await client_async.actor("pratikdani/instagram-posts-scraper").call(run_input=input_object)

        result_posts = asyncio.run(run_actor())
        dataset_id = result_posts.get("defaultDatasetId")
        if not dataset_id:
            print("⚠️ No dataset found for:", instagram_post_url)
            return {}

        dataset_client = apify_client.dataset(dataset_id)
        items = dataset_client.list_items().items
        if not items:
            print("⚠️ No post data found:", instagram_post_url)
            return {}

        item = items[0]

        # Extract raw values
        likes = safe_int(item.get("likes") or 0)
        comments = safe_int(item.get("num_comments") or 0)
        followers = safe_int(item.get("followers") or 0)
        video_play_count = safe_int(item.get("video_play_count") or item.get("video_view_count") or 0)
        engagement_score_view = safe_int(item.get("engagement_score_view") or 0)

        hashtags_val = item.get("hashtags", [])
        hashtags_text = ", ".join(hashtags_val) if isinstance(hashtags_val, list) else only_text(hashtags_val)

        # Determine if Reel/video
        is_reel = video_play_count > 0

        if is_reel:
            # Engagement based on video plays
            engagement_rate = calc_engagement_rate(likes, comments, video_play_count)
            estimated_reach = int(video_play_count * 0.75)  # ~75% of plays as unique reach
        else:
            # Engagement based on followers (static post)
            engagement_rate = calc_engagement_rate(likes, comments, followers)
            estimated_reach = int(followers * 0.40)  # ~40% of followers see the post

        return {
            "instagram_captions": only_text(item.get("caption"))[:500],
            "instagram_hashtags": hashtags_text,
            "instagram_post_urls": only_text(item.get("url")),
            "instagram_comments_counts": str(comments),
            "instagram_video_play_counts": str(video_play_count),
            "instagram_video_urls": only_text(item.get("videos")[0] if item.get("videos") else ""),
            "instagram_likes_counts": str(likes),
            "instagram_engagement_rate": engagement_rate,
            "instagram_reach": str(estimated_reach),
            "engagement_score_view": str(engagement_score_view),
            "instagram_followers": str(followers)
        }

    except Exception as e:
        print("❌ Error in post_scraper:", e)
        return {}

# -----------------------------------
# Scrape All Content & Update Airtable
# -----------------------------------
def scrape_social_post_for_all():
    try:
        content_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "content_submissions")
        influencers_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "influencers_instagram_registered")

        records = content_table.all()
        updated = 0

        for record in records:
            fields = record.get("fields", {})
            social_type = (fields.get("social_media_profile_type") or "").lower()
            influencer_handle = fields.get("influencer_handle")
            instagram_post_url = fields.get("instagram_post_url")

            if social_type != "instagram" or not influencer_handle or not instagram_post_url:
                continue

            influencer_records = influencers_table.all(
                formula=f"{{instagram_username}}='{influencer_handle}'"
            )
            if not influencer_records:
                print(f"⚠️ Influencer not found: {influencer_handle}")
                continue

            instagram_data = post_scraper(instagram_post_url=instagram_post_url)
            if not instagram_data:
                continue

            # Update Airtable
            content_table.update(record["id"], {
                "hashtags_text": instagram_data.get("instagram_hashtags", ""),
                "caption_text": instagram_data.get("instagram_captions", ""),
                "likes": instagram_data.get("instagram_likes_counts", ""),
                "comments": instagram_data.get("instagram_comments_counts", ""),
                "views": instagram_data.get("instagram_video_play_counts", ""),
                "video_play_count": instagram_data.get("instagram_video_play_counts", ""),
                "engagement_rate": instagram_data.get("instagram_engagement_rate", "0%"),
                "engagement_score_view": instagram_data.get("engagement_score_view", 0),
                "reach": instagram_data.get("instagram_reach", 0)
            })
            updated += 1
            print(f"✅ Updated: {influencer_handle}")

        return updated

    except Exception as e:
        print("❌ Error in scrape_social_post_for_all:", e)
        raise