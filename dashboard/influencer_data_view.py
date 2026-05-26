from flask import Blueprint, render_template, jsonify 
import requests

influencer_bp = Blueprint('influencer', __name__, template_folder='../templates')

AIRTABLE_API_KEY = 'patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3'
BASE_ID = 'app5s8zl7DsUaDmtx'
TABLE_NAME = 'src_influencer_data'

# ✅ Add normalized field list
normalized_fields = [
    "business_category_name", "created_time", "email_id", "external_urls", "full_name", "id",
    "influencer_location", "influencer_nationality", "influencer_type", "instagram_bio",
    "instagram_captions", "instagram_comments_counts", "instagram_followers_count",
    "instagram_follows_count", "instagram_hashtags", "instagram_likes_counts",
    "instagram_post_urls", "instagram_posts_count", "instagram_profile_pic", "instagram_url",
    "instagram_username", "instagram_video_play_counts", "instagram_video_urls", "linkedin_url",
    "phone", "profile_type", "snapchat_url", "targeted_audience", "targeted_domain",
    "tiktok_audience_location", "tiktok_bio", "tiktok_comment_count", "tiktok_content_style",
    "tiktok_content_type", "tiktok_digg_count", "tiktok_followers_count", "tiktok_follows_count",
    "tiktok_influencer_summary", "tiktok_language_used", "tiktok_likes_count", "tiktok_niche",
    "tiktok_play_count", "tiktok_profile_pic", "tiktok_share_count", "tiktok_suitable_brands",
    "tiktok_targeted_audience", "tiktok_text", "tiktok_url", "tiktok_username",
    "tiktok_video_urls", "tiktok_videos_count", "twitter_url"
]

@influencer_bp.route("/influencer_data_view", methods=["GET"])
def run_influencer_data_view():
    try:
        return render_template('index.html')
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@influencer_bp.route('/api/influencers', methods=["GET"])
def get_influencer_data():
    airtable_url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}'
    headers = {'Authorization': f'Bearer {AIRTABLE_API_KEY}'}

    all_records = []
    params = {}

    while True:
        response = requests.get(airtable_url, headers=headers, params=params)
        if response.status_code != 200:
            return jsonify({'error': 'Airtable fetch failed'}), 500

        data = response.json()
        all_records.extend(data.get('records', []))

        if 'offset' in data:
            params['offset'] = data['offset']
        else:
            break

    result = []
    for rec in all_records:
        fields = rec.get('fields', {})
        record_data = {field: fields.get(field, '') for field in normalized_fields}

        # Optional: add aliases or extras if needed
        record_data['profile_image'] = fields.get('instagram_profile_pic', '')  # used in JS

        result.append(record_data)

    return jsonify(result)
