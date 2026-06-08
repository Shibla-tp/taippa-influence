import os
import asyncio
from pyairtable import Table
from apify_client import ApifyClientAsync, ApifyClient
from flask import Flask, jsonify, request

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
        print("🔹 Scraper returned item:", item)

        likes = safe_int(item.get("likes") or 0)
        comments = safe_int(item.get("num_comments") or 0)
        followers = safe_int(item.get("followers") or 0)
        video_play_count = safe_int(item.get("video_play_count") or item.get("video_view_count") or 0)
        engagement_score_view = safe_int(item.get("engagement_score_view") or 0)

        hashtags_val = item.get("hashtags", [])
        hashtags_text = ", ".join(hashtags_val) if isinstance(hashtags_val, list) else only_text(hashtags_val)

        is_reel = video_play_count > 0

        if is_reel:
            engagement_rate = calc_engagement_rate(likes, comments, video_play_count)
            estimated_reach = int(video_play_count * 0.75)
        else:
            engagement_rate = calc_engagement_rate(likes, comments, followers)
            estimated_reach = int(followers * 0.40)

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
    
def to_str(val):
    return "" if val is None else str(val)
# -----------------------------------
# Scrape All Content & Update Airtable
# -----------------------------------
def scrape_social_post_for_all(campaign_name):
    try:
        campaign_name = campaign_name.strip().lower()
        content_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "instagram_content_analysis")
        influencers_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "influencers_instagram_registered")

        # Fetch all records
        records = content_table.all()
        print(f"📊 Total content records fetched: {len(records)}")

        # Filter by campaign_name (safe for Long Text)
        filtered_records = [
            r for r in records
            if campaign_name in str(r["fields"].get("campaign_name", "")).lower()
        ]
        print(f"✅ Records matching campaign_name: {len(filtered_records)}")

        updated = 0

        for record in filtered_records:
            fields = record.get("fields", {})
            social_type = str(fields.get("social_media_profile_type") or "").strip().lower()
            influencer_handle = str(fields.get("influencer_handle") or "").strip()
            instagram_post_url = str(fields.get("instagram_post_url") or fields.get("post_url") or "").strip()

            if "instagram" not in social_type or not influencer_handle or not instagram_post_url:
                print("⚠️ Skipping record due to missing/invalid data")
                continue

            # Debug info
            print("🔹 Record fields:", fields)
            print("🔹 social_type:", social_type)
            print("🔹 influencer_handle:", influencer_handle)
            print("🔹 instagram_post_url:", instagram_post_url)

            # Robust social type check
            if "instagram" not in social_type or not influencer_handle or not instagram_post_url:
                print("⚠️ Skipping record due to missing/invalid data")
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

