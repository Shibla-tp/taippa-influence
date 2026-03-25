import os
import asyncio
import json
from pyairtable import Table
from apify_client import ApifyClientAsync, ApifyClient
from flask import Flask, jsonify, request
from openai import OpenAI

app = Flask(__name__)

# -----------------------------------
# Config
# -----------------------------------
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

apify_client = ApifyClient(APIFY_API_TOKEN)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# -----------------------------------
# Utility Functions
# -----------------------------------
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

# -----------------------------------
# GPT Sentiment Analysis
# -----------------------------------
def analyze_sentiment(comments):
    try:
        comment_texts = [c.get("text", "") for c in comments if c.get("text")]

        if not comment_texts:
            return {}

        prompt = f"""
        Analyze the sentiment of the following Instagram comments.

        Return JSON:
        {{
            "overall_sentiment": "positive/neutral/negative",
            "positive": number,
            "neutral": number,
            "negative": number
        }}

        Comments:
        {comment_texts}
        """

        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print("❌ Sentiment error:", e)
        return {}

# -----------------------------------
# Scraper
# -----------------------------------
def post_scraper(instagram_post_url):
    try:
        input_object = {"postUrls": [instagram_post_url]}

        async def run_actor():
            client_async = ApifyClientAsync(APIFY_API_TOKEN)
            return await client_async.actor(
                "powerful_bachelor/instagram-post-details-scraper"
            ).call(run_input=input_object)

        result = asyncio.run(run_actor())
        dataset_id = result.get("defaultDatasetId")

        if not dataset_id:
            return {}

        dataset_client = apify_client.dataset(dataset_id)
        items = dataset_client.list_items().items

        if not items:
            return {}

        item = items[0]

        # ✅ Correct mapping based on your JSON
        likes = safe_int(item.get("like_count", 0))
        comments = safe_int(item.get("comment_count", 0))
        views = safe_int(item.get("video_play_count", 0))
        followers = safe_int(item.get("owner", {}).get("edge_followed_by", {}).get("count", 0))

        # Engagement
        base = views if views > 0 else followers
        engagement_rate = calc_engagement_rate(likes, comments, base)

        # Reach estimation
        reach = int(views * 0.75) if views > 0 else int(followers * 0.40)

        # Sentiment
        latest_comments = item.get("latest_comments", [])
        sentiment = analyze_sentiment(latest_comments)

        return {
            "raw_data": item,  # FULL JSON
            "processed": {
                "caption": item.get("caption", ""),
                "likes": likes,
                "comments": comments,
                "views": views,
                "engagement_rate": engagement_rate,
                "reach": reach,
                "sentiment": sentiment
            }
        }

    except Exception as e:
        print("❌ Scraper error:", e)
        return {}
    
def to_str(val):
    return "" if val is None else str(val)
# -----------------------------------
# Airtable Update
# -----------------------------------
def scrape_social_post_instagram(campaign_name):
    try:
        content_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "instagram_content_analysis")

        records = content_table.all()

        filtered = [
            r for r in records
            if campaign_name.lower() in str(r["fields"].get("campaign_name", "")).lower()
        ]

        updated = 0

        for record in filtered:
            fields = record.get("fields", {})
            url = fields.get("instagram_post_url") or fields.get("post_url")

            if not url:
                continue

            data = post_scraper(url)
            if not data:
                continue

            processed = data.get("processed", {})

            content_table.update(record["id"], {
                "likes": str(processed.get("likes", 0)),
                "comments": str(processed.get("comments", 0)),
                "views": str(processed.get("views", 0)),
                "reach": str(processed.get("reach", 0)),
                "engagement_rate": str(processed.get("engagement_rate", "0%")),
                "sentiment_analysis": json.dumps(processed.get("sentiment", {})),
                # "raw_json": json.dumps(data.get("raw_data", {}))
            })

            updated += 1
            print(f"✅ Updated record {record['id']}")

        return updated

    except Exception as e:
        print("❌ Airtable error:", e)
        return 0

