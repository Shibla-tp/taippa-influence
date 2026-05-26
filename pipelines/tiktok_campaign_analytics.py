import os
import asyncio
import json
from pyairtable import Table
from apify_client import ApifyClient, ApifyClientAsync
from flask import Flask, jsonify, request

# -------------------------------
# Config
# -------------------------------
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, APIFY_API_TOKEN

app = Flask(__name__)

apify_client = ApifyClient(APIFY_API_TOKEN)

# -------------------------------
# Utility Functions
# -------------------------------
def safe_int(val):
    try:
        return int(val)
    except:
        return 0

def calc_engagement_rate(likes, comments, base):
    try:
        if base == 0:
            return "0%"
        return f"{((likes + comments) / base) * 100:.2f}%"
    except:
        return "0%"

# -------------------------------
# Scraper
# -------------------------------
async def run_tiktok_actor(post_url):
    client_async = ApifyClientAsync(APIFY_API_TOKEN)
    run_input = {
        "urls": [post_url]  # ✅ must be list under "urls"
    }
    result = await client_async.actor("logical_scrapers/tiktok-post-scraper").call(run_input=run_input)
    return result

def scrape_tiktok_post(post_url):
    print(f"➡️ Scraping TikTok URL: {post_url}")
    try:
        result = asyncio.run(run_tiktok_actor(post_url))
        dataset_id = result.get("defaultDatasetId")
        if not dataset_id:
            print("❌ No dataset returned by actor.")
            return {}

        dataset_client = apify_client.dataset(dataset_id)
        items = dataset_client.list_items().items
        if not items:
            print("❌ Dataset empty.")
            return {}

        item = items[0]
        print(f"📄 TikTok JSON item: {json.dumps(item, indent=2)[:500]}...")  # Print first 500 chars

        # Extract stats
        likes = safe_int(item.get("stats", {}).get("diggCount", 0))
        comments = safe_int(item.get("stats", {}).get("commentCount", 0))
        shares = safe_int(item.get("stats", {}).get("shareCount", 0))
        saves = safe_int(item.get("stats", {}).get("collectCount", 0))
        views = safe_int(item.get("stats", {}).get("playCount", 0))

        print(f"📊 Extracted stats - Likes: {likes}, Comments: {comments}, Shares: {shares}, Saves: {saves}, Views: {views}")

        # Engagement & Reach
        base = views if views > 0 else 1
        engagement_rate = calc_engagement_rate(likes, comments, base)
        reach = int(views * 0.75) if views > 0 else 0

        print(f"📈 Calculated Engagement Rate: {engagement_rate}, Reach: {reach}")

        return {
            "likes": str(likes),
            "comments": str(comments),
            "shares": str(shares),
            "saves": str(saves),
            "views": str(views),
            "engagement_rate": engagement_rate,
            "reach": str(reach),
            "caption": item.get("desc", ""),
            "author_name": item.get("author", {}).get("nickname", ""),
            "author_id": item.get("author", {}).get("uniqueId", ""),
            "video_url": item.get("video", {}).get("playAddr", "")
        }

    except Exception as e:
        print("❌ Scraper error:", e)
        return {}

# -------------------------------
# Airtable Update
# -------------------------------
def scrape_social_post_tiktok(campaign_name):
    table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "tiktok_content_analysis")
    records = table.all()

    filtered = [
        r for r in records
        if campaign_name.lower() in str(r.get("fields", {}).get("campaign_name", "")).lower()
    ]

    updated = 0
    for record in filtered:
        fields = record.get("fields", {})
        post_url = fields.get("post_url")
        if not post_url:
            print(f"❌ Record {record['id']} missing post_url")
            continue

        data = scrape_tiktok_post(post_url)
        if not data:
            continue

        table.update(record["id"], {
            "likes": data.get("likes", ""),
            "comments": data.get("comments", ""),
            "shares": data.get("shares", ""),
            "saves": data.get("saves", ""),
            "views": data.get("views", ""),
            "engagement_rate": data.get("engagement_rate", ""),
            "reach": data.get("reach", ""),
            "caption_text": data.get("caption", ""),
            # "author_name": data.get("author_name", ""),
            # "author_id": data.get("author_id", ""),
            # "video_url": data.get("video_url", "")
        })

        updated += 1
        print(f"✅ Updated record {record['id']}")

    return updated

