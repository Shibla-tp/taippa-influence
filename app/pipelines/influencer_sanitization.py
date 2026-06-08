from flask import Flask, request, jsonify
import re

app = Flask(__name__)

FIELDS = [
    "avg_comments", "avg_likes", "avg_video_play_counts", "business_category_name",
    "created_time", "email_id", "external_urls", "full_name", "id", "influencer_location",
    "influencer_nationality", "influencer_type", "instagram_bio", "instagram_captions",
    "instagram_comments_counts", "instagram_followers_count", "instagram_follows_count",
    "instagram_hashtags", "instagram_likes_counts", "instagram_post_urls",
    "influencer_nationality", "influencer_type", "instagram_bio", 
    "instagram_comments_counts", "instagram_followers_count", "instagram_follows_count",
    "instagram_likes_counts", "instagram_post_urls",
    "instagram_posts_count", "instagram_profile_pic", "instagram_url", "instagram_username",
    "instagram_video_play_counts", "instagram_video_urls", "linkedin_url", "phone",
    "profile_type", "snapchat_url", "social_media_profile_type", "targeted_audience",
    "targeted_domain", "tiktok_url", "twitter_url", "engagement_rate", "estimated_reach"
]

# === Cleaning Helpers ===
def clean_value(value):
    if isinstance(value, str) and value.strip().lower() in {"na", "n/a", "none", ""}:
        return ""
    return value

def clean_email(email):
    if isinstance(email, str):
        email = email.strip().lower()
        return email if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) else ""
    return ""

def clean_phone(phone):
    if not isinstance(phone, str):
        return ""

    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone)

    if not digits:
        return ""

    # Remove leading zeros or country code
    if digits.startswith("966"):
        digits = digits[3:]
    elif digits.startswith("00966"):
        digits = digits[5:]
    elif digits.startswith("0"):
        digits = digits[1:]

    # Ensure it's 9 digits long (typical for Saudi mobile numbers)
    if len(digits) == 9:
        return f"+966{digits}"
    else:
        return ""


def is_valid_ig_url(url):
    return isinstance(url, str) and re.match(r"^https?://(www\.)?instagram\.com/(?!reel)[^/?#]+/?", url)

def is_valid_tt_url(url):
    return isinstance(url, str) and url.strip().startswith("https://www.tiktok.com/")

# === Clean & Return Without Saving ===
def sanitize_data_instagram(data_list):
    cleaned_results = []
    skipped_count = 0

    for index, fields in enumerate(data_list):
        social_type = (fields.get("social_media_profile_type") or "").strip().lower()
        ig_url = (fields.get("instagram_url") or "").strip()
        tt_url = (fields.get("tiktok_url") or "").strip()

        # Validate social URL
        if social_type == "instagram" and not is_valid_ig_url(ig_url):
            skipped_count += 1
            continue
        if social_type == "tiktok" and not is_valid_tt_url(tt_url):
            skipped_count += 1
            continue

        cleaned = {}
        for field in FIELDS:
            val = clean_value(fields.get(field, ""))
            if field == "email_id":
                val = clean_email(val)
            elif field == "phone":
                val = clean_phone(val)
            elif field == "id":
                val = str(val)
            elif field == "engagement_rate":
                val = str(val)
            elif field == "estimated_reach":
                val = str(val)
            cleaned[field] = val

        cleaned_results.append(cleaned)

    return {
        "total_input": len(data_list),
        "cleaned_count": len(cleaned_results),
        "skipped_count": skipped_count,
        "cleaned_data": cleaned_results
    }
