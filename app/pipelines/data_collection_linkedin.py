import os
import requests
import json
import time
from datetime import datetime, timezone
from apify_client import ApifyClient
import asyncio
import nest_asyncio
from apify_client import ApifyClient, ApifyClientAsync
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS,APIFY_API_TOKEN
from pyairtable import Table,Api

# --------------------------------------------------
# 🔐 CONFIG (FROM config.py)
# --------------------------------------------------

APIFY_TOKEN = APIFY_API_TOKEN
AIRTABLE_TOKEN = AIRTABLE_API_KEY
BASE_ID = AIRTABLE_BASE_ID
TABLE_NAME = "influencers_linkedin_v3"

ACTOR_1 = "apimaestro/linkedin-profile-detail"
ACTOR_2 = "dev_fusion/Linkedin-Profile-Scraper"

AIRTABLE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

client = ApifyClient(APIFY_TOKEN)

SOURCE_TABLE_NAME = "linkedin_source"

SOURCE_AIRTABLE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{SOURCE_TABLE_NAME}"


# --------------------------------------------------
# 🟢 HELPERS
# --------------------------------------------------

def normalize_url(url):
    if not url:
        return None

    url = url.strip().lower()
    url = url.replace("https://", "").replace("http://", "")
    url = url.replace("www.", "")
    url = url.rstrip("/")

    if "?" in url:
        url = url.split("?")[0]

    return url


def safe_int(value):
    try:
        return int(value)
    except:
        return 0

def to_text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)
# --------------------------------------------------
# 🟢 FETCH EXISTING URLs
# --------------------------------------------------
def extract_public_id(url):
    if not url:
        return None

    url = url.strip().lower()

    # Remove protocol
    url = url.replace("https://", "").replace("http://", "")
    url = url.replace("www.", "")

    # Remove query params
    if "?" in url:
        url = url.split("?")[0]

    # Find /in/
    if "/in/" not in url:
        return None

    username = url.split("/in/")[1]

    # Remove anything after username
    username = username.split("/")[0]

    return username.strip()


def get_all_existing_urls():
    existing = set()
    offset = None

    while True:
        params = {}
        if offset:
            params["offset"] = offset

        response = requests.get(AIRTABLE_URL, headers=HEADERS, params=params)

        if response.status_code != 200:
            print("Airtable fetch error:", response.text)
            break

        data = response.json()
        
        for record in data.get("records", []):
            public_id = record["fields"].get("public_identifier")
            if public_id:
                existing.add(public_id.lower())

        offset = data.get("offset")
        if not offset:
            break

    return existing


# --------------------------------------------------
# 🟢 ACTOR CALLS
# --------------------------------------------------

def scrape_actor1(linkedin_url):

    run_input = {
        "username": linkedin_url,
        "includeEmail": True
    }

    run = client.actor(ACTOR_1).call(run_input=run_input)
    dataset_id = run["defaultDatasetId"]

    return list(client.dataset(dataset_id).iterate_items())


def scrape_actor2(linkedin_url):

    run_input = {
        "profileUrls": [linkedin_url]
    }

    run = client.actor(ACTOR_2).call(run_input=run_input)
    dataset_id = run["defaultDatasetId"]

    results = list(client.dataset(dataset_id).iterate_items())
    return results[0] if results else {}


# --------------------------------------------------
# 🟢 LOCATION
# --------------------------------------------------

def extract_city_country(location):

    if not location:
        return "", ""

    if isinstance(location, str):
        parts = location.split(",")
        if len(parts) >= 2:
            return parts[0].strip(), parts[-1].strip()
        return "", location.strip()

    if isinstance(location, dict):
        return location.get("city", ""), location.get("country", "")

    return "", ""

# --------------------------------------------------
# 🟢 POSTS + METRICS
# --------------------------------------------------

def extract_post_data(featured):

    post_urls, likes, comments, reaction_counts = [], [], [], []

    if not featured:
        return post_urls, likes, comments, reaction_counts

    for post in featured:
        post_urls.append(post.get("url"))

        social = post.get("social_counts", {})
        likes.append(safe_int(social.get("likes")))
        comments.append(safe_int(social.get("comments")))

        if social.get("reaction_counts"):
            reaction_counts.append(social.get("reaction_counts"))

    return post_urls, likes, comments, reaction_counts


def calculate_average(numbers):
    clean = [safe_int(n) for n in numbers]
    return round(sum(clean) / len(clean), 2) if clean else 0


def calculate_weighted_reaction_score(reaction_counts):

    weights = {
        "like": 1,
        "praise": 2,
        "empathy": 1.5,
        "appreciation": 1.2,
        "interest": 1.3
    }

    total = 0

    for post in reaction_counts:
        for reaction in post:
            r_type = reaction.get("type", "").lower()
            count = safe_int(reaction.get("count"))
            total += count * weights.get(r_type, 1)

    return round(total, 2)


def calculate_engagement_rate(avg_likes, avg_comments, followers):
    followers = safe_int(followers)
    if followers == 0:
        return 0
    return round(((avg_likes + avg_comments) / followers) * 100, 2)


def calculate_influence_score(followers, engagement_rate):
    followers = safe_int(followers)
    return round((followers * 0.001) + (engagement_rate * 10), 2)


def calculate_viral_score(avg_likes, avg_comments):
    return round((avg_likes * 0.6) + (avg_comments * 1.2), 2)


def determine_tier(followers):
    followers = safe_int(followers)
    if followers >= 1_000_000:
        return "Mega"
    elif followers >= 100_000:
        return "Macro"
    elif followers >= 50_000:
        return "Mid"
    elif followers >= 10_000:
        return "Micro"
    return "Nano"

# --------------------------------------------------
# 🟢 SAVE TO AIRTABLE
# --------------------------------------------------

def save_to_airtable(actor1_data, actor2_data):

    for item in actor1_data:

        basic = item.get("basic_info", {})
        # linkedin_url = basic.get("profile_url")
        linkedin_url = normalize_url(basic.get("profile_url"))
        


        followers = safe_int(basic.get("follower_count"))

        post_urls, likes, comments, reaction_counts = extract_post_data(
            item.get("featured")
        )

        avg_likes = calculate_average(likes)
        avg_comments = calculate_average(comments)
        weighted_score = calculate_weighted_reaction_score(reaction_counts)
        engagement_rate = calculate_engagement_rate(avg_likes, avg_comments, followers)
        influence_score = calculate_influence_score(followers, engagement_rate)
        viral_score = calculate_viral_score(avg_likes, avg_comments)
        tier = determine_tier(followers)

        address = basic.get("location")
        city, country = extract_city_country(address)

        created_timestamp = basic.get("created_timestamp")

        account_age = ""
        if created_timestamp:
            try:
                created_dt = datetime.fromtimestamp(
                    int(created_timestamp) / 1000,
                    tz=timezone.utc
                )
                account_age = (datetime.now(timezone.utc) - created_dt).days
            except:
                pass

        payload = {
            "fields": {

                # ---------------- ACTOR 1 ----------------

                # "linkedin_url": to_text(linkedin_url),
                "public_identifier": to_text(basic.get("public_identifier")),
                "linkedin_id": to_text(basic.get("urn")),
                "linkedin_url": linkedin_url,
                "full_name": to_text(basic.get("fullname")),
                "headline": to_text(basic.get("headline")),
                "about": to_text(basic.get("about")),
                "creator_hashtags": to_text(basic.get("creator_hashtags")),

                "linkedin_followers": to_text(followers),
                "linkedin_connections": to_text(basic.get("connection_count")),

                

                # Actor 1 default (will be overridden if Actor 2 has value)
                "company_name": to_text(
                    actor2_data.get("companyName") or basic.get("current_company")
                ),
                "company_website": to_text(
                    actor2_data.get("companyWebsite") or basic.get("current_company_url")
                ),
                "company_linkedin_url": to_text(
                    actor2_data.get("companyLinkedin") or basic.get("companyLinkedin")
                ),
                "address_with_country": to_text(address),
                "city": to_text(city),
                "country": to_text(country),

                "linkedin_profile_pic": to_text(basic.get("profile_picture_url")),
                "is_premium": to_text(basic.get("is_premium")),
                "is_creator": to_text(
                    actor2_data.get("isCreator") or basic.get("is_creator")
                ),
                "is_influencer": to_text(basic.get("is_influencer")),

                "employment_history": to_text(item.get("experience")),
                "education_history": to_text(item.get("education")),

                # skills: actor2 priority
                "skills": to_text(
                    actor2_data.get("skills") or basic.get("top_skills")
                ),

                "email": to_text(actor2_data.get("email")),
                "phone": to_text(actor2_data.get("mobileNumber")),
                "job_title": to_text(actor2_data.get("jobTitle")),

                "post_urls": to_text(post_urls),
                "likes": to_text(likes),
                "comments": to_text(comments),
                "reaction_counts": to_text(reaction_counts),

                "avg_likes": to_text(avg_likes),
                "avg_comments": to_text(avg_comments),
                "engagement_rate": to_text(engagement_rate),
                "weighted_reaction_score": to_text(weighted_score),
                "influence_score": to_text(influence_score),
                "viral_score": to_text(viral_score),
                "influencer_tier": to_text(tier),

                "created_at": to_text(created_timestamp),
                "account_age": to_text(account_age),
                "scraped_at": to_text(datetime.now(timezone.utc).isoformat())
            }
        }

        response = requests.post(AIRTABLE_URL, headers=HEADERS, json=payload)

        print("Status:", response.status_code)
        print(response.text)

        time.sleep(0.4)
# --------------------------------------------------
# 🟢 MAIN PROCESS FUNCTION
# --------------------------------------------------

def process_linkedin_profiles(profile_urls):

    results = []
    existing_urls = get_all_existing_urls()
   

    for profile in profile_urls:

        # normalized = normalize_url(profile)
        normalized = extract_public_id(profile)

        
        if not normalized:
            results.append({
                "profile": profile,
                "status": "invalid_url"
            })
            continue

        if normalized in existing_urls:
            results.append({
                "profile": profile,
                "status": "duplicate_skipped"
            })
            continue

        try:
            actor1_data = scrape_actor1(profile)
            actor2_data = scrape_actor2(profile)

            save_to_airtable(actor1_data, actor2_data)

            existing_urls.add(normalized)

            results.append({
                "profile": profile,
                "status": "saved"
            })

        except Exception as e:
            results.append({
                "profile": profile,
                "status": "error",
                "error": str(e)
            })

    return results

def get_profiles_from_source():

    profiles = []
    offset = None

    while True:
        params = {}
        if offset:
            params["offset"] = offset

        print("SOURCE URL:", SOURCE_AIRTABLE_URL)

        response = requests.get(
            SOURCE_AIRTABLE_URL,
            headers=HEADERS,
            params=params
        )

        print(response.status_code)
        print(response.text)

        if response.status_code != 200:
            print("Error fetching source table:", response.text)
            break

        data = response.json()

        for record in data.get("records", []):
            url = record["fields"].get("linkedin_profile_url")
            if url:
                profiles.append(url)

        offset = data.get("offset")
        if not offset:
            break

    return profiles
