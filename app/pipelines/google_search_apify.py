import requests
import re
from flask import Flask, jsonify, request
from config import (
    OPENAI_API_KEY, AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME,
    APOLLO_API_KEY, APOLLO_HEADERS, APIFY_API_TOKEN
)

app = Flask(__name__)

APIFY_API_URL = f"https://api.apify.com/v2/acts/tuningsearch~cheap-google-search-results-scraper/run-sync-get-dataset-items?token={APIFY_API_TOKEN}"

# === Airtable config ===
AIRTABLE_TABLE_NAME = 'influencer_profile_urls_v3'
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}


from urllib.parse import unquote

def extract_username(url, media):
    url = unquote(url)

    if media == "instagram":
        # Skip non-profile Instagram paths
        if any(x in url for x in ["/reel/", "/reels/", "/p/", "/tv/", "/stories/", "/explore/"]):
            return None
        match = re.search(r"instagram\.com/([a-zA-Z0-9_.]+)", url)

    elif media == "tiktok":
        if any(x in url for x in ["/discover/", "/hashtag/"]):
            return None
        match = re.search(r"tiktok\.com/@([^/?#]+)", url)
        if not match:
            match = re.search(r"tiktok\.com/@([^/]+)/video", url)

    return match.group(1) if match else None


# === Check for duplicate using unique_profile_key ===
def is_duplicate(unique_profile_key):
    filter_formula = f"{{unique_profile_key}} = '{unique_profile_key}'"
    params = {"filterByFormula": filter_formula}
    response = requests.get(AIRTABLE_URL, headers=HEADERS, params=params)
    if response.status_code == 200:
        records = response.json().get("records", [])
        return len(records) > 0
    else:
        print(f"⚠️ Error checking duplicate for {unique_profile_key}: {response.text}")
        return False


# === Add new record to Airtable ===
def add_to_airtable(media, username, url, influencer_type, influencer_location, search_query):
    if not username:
        return

    unique_key = f"{media.lower()}_{username}"

    fields = {
        "username": username,
        "social_media_type": media.lower(),
        "profile_url": url,
        "unique_profile_key": unique_key,
        "influencer_type": influencer_type,
        "influencer_location": influencer_location,
        "search_query": search_query
    }

    data = {"fields": fields}

    response = requests.post(AIRTABLE_URL, headers=HEADERS, json=data)
    if response.status_code in [200, 201]:
        record_id = response.json().get('id')
        print(f"✅ Added to Airtable: {username} ({media}) | Record ID: {record_id}")
    else:
        print(f"❌ Failed to add {username}: {response.text}")


def process_and_upload(results, media, influencer_type, influencer_location, search_query):
    seen = set()
    skipped_urls = []  # collect non-profile/invalid URLs

    for item in results:
        url = item.get("url", "")
        username = extract_username(url, media)
        if username:
            unique_key = f"{media.lower()}_{username}"
            if unique_key not in seen:
                seen.add(unique_key)
                if not is_duplicate(unique_key):
                    profile_url = f"https://www.{media}.com/@{username}" if media == "tiktok" else url
                    add_to_airtable(media, username, profile_url, influencer_type, influencer_location, search_query)
                else:
                    print(f"🔁 Skipped duplicate: {unique_key}")
            else:
                print(f"⚠️ Already seen: {unique_key}")
        else:
            skipped_urls.append(url)
            print(f"⚠️ Skipped invalid username for URL: {url}")
    
    return skipped_urls  # return this if needed

# === Main scraping logic ===
def scrape_influencers(data, media, influencer_type, influencer_location, page):
    if not (media and influencer_type and influencer_location):
        return jsonify({"error": "Missing required params"}), 400

    if request.method == 'GET':
        search_query = f"{media} {influencer_type} in {influencer_location}"
    else:
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400
        search_query = data.get("query")
        if not search_query:
            return jsonify({"error": "Missing 'query' in request body"}), 400

    print(f"📡 Triggering Apify scrape: {search_query} | Page {page}")

    payload = {
        "language": "en",
        "query": search_query,
        "page": page
    }

    response = requests.post(APIFY_API_URL, json=payload)

    if response.ok:
        try:
            results = response.json()
            print(f"📦 Scraped {len(results)} URLs")
            skipped = process_and_upload(results, media, influencer_type, influencer_location, search_query)

            return jsonify({
                "message": "Scraping complete, data uploaded to Airtable",
                "query": search_query,
                "page": page,
                "results_count": len(results),
                "skipped_urls": skipped  # non-profile / invalid TikTok links
            }), 200

        except Exception as e:
            return jsonify({"error": "Failed to parse Apify results", "details": str(e)}), 500
    else:
        return jsonify({
            "error": "Apify API error",
            "status": response.status_code,
            "details": response.text
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
