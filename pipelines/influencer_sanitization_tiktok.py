from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# === Fields matching normalized TikTok Airtable structure ===
FIELDS = [
    "created_time", "email_id", "external_urls", "full_name", "id", "influencer_location",
    "influencer_nationality", "influencer_type", "instagram_url", "phone", "profile_type",
    "social_media_profile_type", "targeted_audience", "tiktok_audience_location", "tiktok_bio",
    "tiktok_comment_count", "tiktok_content_style", "tiktok_content_type", "tiktok_digg_count",
    "tiktok_followers_count", "tiktok_follows_count", "tiktok_influencer_summary", "tiktok_language_used",
    "tiktok_likes_count", "tiktok_niche", "tiktok_play_count", "tiktok_profile_pic", "tiktok_share_count",
    "tiktok_suitable_brands", "tiktok_targeted_audience", "tiktok_text", "tiktok_url", "tiktok_username",
    "tiktok_video_urls", "tiktok_videos_count"
]

# === Cleaning Helpers ===
def clean_value(value):
    if isinstance(value, str) and value.strip().lower() in {"na", "n/a", "none", "unknown", ""}:
        return ""
    return value

def clean_email(email):
    if isinstance(email, str):
        email = email.strip().lower()
        return email if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) else ""
    return ""

def clean_phone(phone):
    if isinstance(phone, str):
        digits = re.sub(r"\D", "", phone)
        return f"+{digits}" if digits else ""
    return ""

def is_valid_tt_url(url):
    return isinstance(url, str) and url.strip().startswith("https://www.tiktok.com/")

# === Clean & Return Without Saving ===
def sanitize_and_upload_tiktok_data(data_list):
    cleaned_results = []
    skipped_count = 0
    print(f"Data for cleaning:{data_list}")
    for index, fields in enumerate(data_list):
        social_type = (fields.get("social_media_profile_type") or "").strip().lower()
        tt_url = (fields.get("tiktok_url") or "").strip()

        # Skip if not valid TikTok profile
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
            cleaned[field] = val

        cleaned_results.append(cleaned)
    print(f"cleaned Data: {cleaned_results}")

    return {
        "total_input": len(data_list),
        "cleaned_count": len(cleaned_results),
        "skipped_count": skipped_count,
        "cleaned_data": cleaned_results
    }



# === Run App ===
if __name__ == "__main__":
    app.run(debug=True)
