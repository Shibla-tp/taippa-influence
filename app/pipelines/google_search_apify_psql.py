import re
from flask import jsonify, request
from db.db_ops import db_manager 

# === Apify config ===
APIFY_TOKEN = "apify_api_OzlpdlQM48B0bXW6gKThLiVYz5nIcS35jGvl"
APIFY_API_URL = f"https://api.apify.com/v2/acts/tuningsearch~cheap-google-search-results-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"


# === Extract username from URL for Instagram or TikTok ===
def extract_username(url):
    if "instagram.com" in url:
        # Skip reels
        if "/reel/" in url or "/reels/" in url:
            return None
        match = re.search(r"instagram\.com/([^/?#]+)", url)
    elif "tiktok.com" in url:
        match = re.search(r"tiktok\.com/@([^/?#]+)", url)
    else:
        return None
    return match.group(1) if match else None




# === Process scraped results and upload to PostgreSQL ===
def process_and_upload(results, media, influencer_type, influencer_location, search_query):
    seen = set()
    for item in results:
        url = item.get("url", "")
        username = extract_username(url)
        unique_profile_key = f"{media}_{username}"

        if username and unique_profile_key not in seen:
            seen.add(unique_profile_key)
            is_dup = db_manager.unique_key_check("unique_profile_key", unique_profile_key, "influencer_profile_urls")
            if not is_dup:
                fields = {
                    "unique_profile_key": unique_profile_key,
                    "social_media_type": media,
                    "username": username,
                    "profile_url": url,
                    "search_query": search_query,
                    "influencer_type": influencer_type,
                    "influencer_location": influencer_location
                }
                db_manager.insert_data("influencer_profile_urls", fields)
                print(f"✅ Inserted: {username}")
            else:
                print(f"🔁 Skipped duplicate: {username}")
        else:
            print(f"⚠️ Invalid or already seen username: {username}")

# === Flask route function to trigger scraping ===
def scrape_influencers_psql(data, media, influencer_type, influencer_location, page):
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

    import requests  # Only needed for Apify API
    response = requests.post(APIFY_API_URL, json=payload)

    if response.ok:
        results = response.json()
        print(f"✅ Retrieved {len(results)} results from Apify")
        process_and_upload(results, media, influencer_type, influencer_location, search_query)
        return jsonify({
            "message": "Scraping complete, data uploaded to PostgreSQL",
            "query": search_query,
            "page": page,
            "results_count": len(results)
        }), 200
    else:
        return jsonify({
            "error": "Apify API error",
            "status": response.status_code,
            "details": response.text
        }), 500
