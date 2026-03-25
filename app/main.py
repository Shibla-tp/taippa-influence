############################################# Code to Perform Smart Data Mining ############################################# 

# Package imports
import os
from flask import Flask, render_template, request, jsonify
from urllib.parse import unquote
import time
import ast
import json
import traceback
import asyncio
import pytz
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS,APIFY_API_TOKEN
from pyairtable import Table,Api
from pipelines.data_sanitization import fetch_and_update_data, update_email_opens, test_sanitize
from pipelines.data_sanitization import update_email_opens
from pipelines.data_extractor import people_enrichment,test_run_pipeline,run_demo_pipeline
from pipelines.guideline_data_sync import parse_contacts,influencer_marketing
from db.table_creation import create_client_tables
from pipelines.icp_generation import generate_icp,generate_apollo_url
from db.db_utils import fetch_client_details,export_to_airtable,unique_key_check_airtable,parse_people_info,add_client_tables_info,add_apollo_webhook_info,fetch_latest_created_time,fetch_record_count_after_time,phone_number_updation
from error_logger import execute_error_block
from lead_magnet.lead_magnet_pdf_generation import generate_lead_magnet_pdf,test_run
from pipelines.data_sync import trigger_pipeline_custom,trigger_custom_pipeline
from pipelines.lead_website_analysis import chroma_db_testing,web_analysis
from pipelines.login_email_confirmation import login_email_sender
from outreach.add_leads import add_lead_leadsin
from outreach.campaign_metrics import update_linkedin_campaign_metrics
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS
from dashboard.dashboard_updation import process_whatsapp_data
from dashboard.client_onboarding_update_form import update_client_onboarding
from dashboard.client_configuration_form import update_client_configuration
from dashboard.client_profile_picture import get_profile_picture
from dashboard.email_dashboard import fetch_recent_leads_from_db, fetch_metric_value, get_booking_count, email_sent_chart, get_campaign_details, fetch_leads, get_user_campaigns, get_campaign_metrics, get_lead_details
from dashboard.leads_email import generate_csv_and_send_email
from dashboard.test_databse import run_database_test
from dashboard.linkedin_dashboard import get_linkedin_metrics, get_linkedin_campaign_details, get_linkedin_statistics, get_linkedin_replies, get_linkedin_leads_by_username
from pipelines.organization_list_enrichment import fetch_organization_domains
# from pipelines.guideline_generate import generate_content_guideline
from pipelines.data_sanitization_psql import sanitize_data
from pipelines.guideline_generate import execute_generate_sequence
from pipelines.guideline_outreach import execute_outreach_sequence

from make.linkedIn_message_sent_tracker import linkedin_message_sent_tracker
from make.linkedIn_invite_sent_tracker import linkedin_invite_sent_tracker
from make.linkedIn_invite_accepted_tracker import linkedin_invite_accepted_tracker
from make.email_sent import email_sent_tracker
from make.ai_response_module import linkedin_ai_response_tracker
from email_module.generic_email_module import send_html_email
from make.email_post_response import email_post_response_tracker
from make.booking_records_for_taippa import booking_meeting_tracker
from make.booking_meeting_form_submition import booking_meeting_form_tracker
from pipelines.data_collection_influencers import data_collection,profile_scraper,post_scraper,add_influencer_to_db

from pipelines.data_collection_influencers import data_collection

from pipelines.smart_query_engine import convert_text_to_sql_v2
from db.db_influencer import influencer_table_trigger
# from pipelines.tiktok import scrape_multiple_profiles

from pipelines.data_collection_influencers_tiktok import scrape_tiktok_profile
from pipelines.data_collection_influencers_tiktok_psql import scrape_tiktok_profile_psql
from pipelines.data_enrtichment_tiktok import scrape_and_store
from pipelines.data_enrtichment_tiktok_psql import scrape_and_store_psql

from pipelines.data_collection_influencers_tiktok import scrape_tiktok_profile
from pipelines.data_enrtichment_tiktok import scrape_and_store
from pipelines.retrieve_influencer_data import retrieve_data_from_db
from pipelines.profile_analyzer_engine import profile_intelligence_engine
# from pipelines.smart_query_machine import influencer_brief_processing
from pipelines.estimated_reach_engagement_rate import calculate_metrics
from pipelines.google_search_apify import scrape_influencers
from db.db_influencer import export_influencer_data
from db.db_ops import db_manager

from pipelines.google_search_apify_psql import scrape_influencers_psql
from pipelines.data_gpt_enritchement_psql import data_entrichment_using_gpt
from influencers.ai_query_engine import airtable_formula_generator,fetch_records_from_airtable_with_formula
from influencers.process_brand_brief import influencer_brief_processing
# from make.influencer_marketing_landing_page_form import influencer_form_tracker
from pipelines.influencer_sanitization import  sanitize_data_instagram
from pipelines.influencer_sanitization_tiktok import sanitize_and_upload_tiktok_data
from pipelines.data_gpt_enritchement import data_entrichment_using_gpt_airtable
from dashboard.influencer_registration_form import handle_upload_and_submit_to_airtable
from pipelines.image_recognition import extract_images
from pipelines.image_recognition_without_airtable import image_analysis_endpoint
from pipelines.profile_pic import process_and_upload_image
from pipelines.profile_pic_with_airtable import process_and_upload_image_with_airtable
from pipelines.campaign_metrics_tracker import update_campaign_metrics_v3
from pipelines.registered_influencer_sanitization import clean_data
from influencers.notion_content_extractor import get_notion_page_text
from influencers.process_meeting_notes import populate_meeting_notes
from pipelines.process_external_url import extract_info
from pipelines.analytics_of_campaign import scrape_social_post_for_all
# from pipelines.database_updation import profile_scraper, post_scraper, download_and_upload_profile_pic, download_and_upload_post_media
from pipelines.data_collection_linkedin import  get_profiles_from_source, process_linkedin_profiles
from pipelines.data_collection_linkedin_profile_pic import process_all_profile_pics
from pipelines.instagram_campaign_analytics import scrape_social_post_instagram
print(f"\n =============== Generate : Pipeline started  ===============")

print(f" Directory path for main file: {os.path.dirname(os.path.abspath(__file__))}")
print('Starting the app')
app = Flask(__name__)
# app.register_blueprint(influencer_bp)
import ast  

@app.route("/process-profile-pics", methods=["GET"])
def process_profile_pics():
    result = process_all_profile_pics()
    return jsonify(result)

@app.route("/scrape-linkedin", methods=["GET"])
def scrape_linkedin():

    profiles = get_profiles_from_source()

    if not profiles:
        return jsonify({"error": "No profiles found in linkedin_source"}), 400

    results = process_linkedin_profiles(profiles)

    return jsonify({
        "status": "completed",
        "total_profiles": len(profiles),
        "results": results
    })
@app.route("/update_registered_post_urls", methods=["GET"])
def update_registered_post_urls():

    try:
        target_table = Table(
            AIRTABLE_API_KEY,
            AIRTABLE_BASE_ID,
            "influencers_instagram_registered"
        )

        records = target_table.all()
        target_date = "2026-02-20"

        for rec in records:

            fields = rec.get("fields", {})
            record_id = rec.get("id")
            instagram_handle = fields.get("instagram_username")
            last_scraped = fields.get("last_scraped_at")

            if not instagram_handle or not last_scraped:
                continue

            # Extract only date part
            try:
                last_scraped_date = last_scraped.split("T")[0]
            except:
                last_scraped_date = last_scraped[:10]

            if last_scraped_date != target_date:
                continue

            username = instagram_handle.strip().lstrip("@")
            print(f"🔄 Updating posts for {username}...")

            # -------- POSTS SCRAPER --------
            post_data = post_scraper(username, 5) or {}

            # -------- UPDATE ONLY REQUIRED FIELDS --------
            update_data = {

                "instagram_captions": str(post_data.get("instagram_captions", "")),
                "instagram_hashtags": str(post_data.get("instagram_hashtags", "")),
                "instagram_post_urls": str(post_data.get("instagram_post_urls", "")),
                "instagram_comments_counts": str(post_data.get("instagram_comments_counts", "")),
                "instagram_likes_counts": str(post_data.get("instagram_likes_counts", "")),
                "instagram_video_urls": str(post_data.get("instagram_video_urls", "")),
                "instagram_video_play_counts": str(post_data.get("instagram_video_play_counts", "")),

                # Optional: update scrape timestamp
                "last_scraped_at": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
            }

            target_table.update(record_id, update_data)

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)})
    
@app.route("/update_registered_influencers_all", methods=["GET"])
def update_registered_influencers_all():

    try:
        target_table = Table(
            AIRTABLE_API_KEY,
            AIRTABLE_BASE_ID,
            "influencers_instagram_registered"
        )

        records = target_table.all()
        target_date = "2026-02-16"

        for rec in records:

            fields = rec.get("fields", {})
            record_id = rec.get("id")
            instagram_handle = fields.get("instagram_username")

            if not instagram_handle:
                continue

            username = instagram_handle.strip().lstrip("@")

           
            last_scraped = fields.get("last_scraped_at")

            if not instagram_handle or not last_scraped:
                continue

            normalized_handle = instagram_handle.strip().lstrip("@")

            # ---- Check if last_scraped_at date matches target_date ----
            try:
                last_scraped_date = last_scraped.split("T")[0]  # Extract date part only
            except:
                last_scraped_date = last_scraped[:10]  # Fallback: take first 10 chars

            if last_scraped_date != target_date:
                continue  # Skip if date doesn't match

            print(f"🔄 Updating {normalized_handle} (last_scraped_at date = {target_date})...")
            # -------- PROFILE --------

            profile_data = profile_scraper(username) or {}

            profile_drive_link = None
            if profile_data.get("instagram_profile_pic"):
                profile_drive_link = download_and_upload_profile_pic(
                    profile_data["instagram_profile_pic"],
                    username
                )

            # -------- POSTS --------

            post_data = post_scraper(username, 5) or {}

            media_urls = ast.literal_eval(
                post_data.get("instagram_video_urls", "[]")
            )

            post_drive_links = []

            for idx, media_url in enumerate(media_urls, start=1):
                link = download_and_upload_post_media(
                    media_url,
                    username,
                    idx
                )
                if link:
                    post_drive_links.append(link)
                time.sleep(1)

            # -------- UPDATE AIRTABLE --------

            update_data = {

                # Profile info
                "instagram_bio": str(profile_data.get("instagram_bio", "")),
                "instagram_profile_pic": str(profile_data.get("instagram_profile_pic", "")),

                # Drive link (text field)
                "downloadable_profile_pic": str(profile_drive_link or ""),

                # ✅ Attachment field (MUST be type: Attachment in Airtable)
                "saved_profile_pic": (
                    [{"url": profile_drive_link}]
                    if profile_drive_link else []
                ),

                "instagram_followers_count": str(profile_data.get("instagram_followers_count", "")),
                "instagram_follows_count": str(profile_data.get("instagram_follows_count", "")),
                "instagram_posts_count": str(profile_data.get("instagram_posts_count", "")),

                # Posts info
                "instagram_video_urls": str(post_data.get("instagram_video_urls", "")),
                "instagram_comments_counts": str(post_data.get("instagram_comments_counts", "")),
                "instagram_likes_counts": str(post_data.get("instagram_likes_counts", "")),
                "instagram_video_play_counts": str(post_data.get("instagram_video_play_counts", "")),

                "avg_likes": str(post_data.get("avg_likes", "")),
                "avg_comments": str(post_data.get("avg_comments", "")),
                "avg_video_play_counts": str(post_data.get("avg_video_play_counts", "")),
                "videos_engagement": str(post_data.get("avg_video_play_counts", "")),

                "drive_post_links": str(post_drive_links),

                "last_scraped_at": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
            }

            target_table.update(record_id, update_data)

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)})
    
@app.route("/scrape-post", methods=["GET", "POST"])
def scrape_post_api():
    try:
        # GET → query param
        if request.method == "GET":
            campaign_name = request.args.get("campaign_name")

        # POST → JSON body
        else:
            data = request.get_json()
            campaign_name = data.get("campaign_name") if data else None

        if not campaign_name:
            return jsonify({
                "status": "error",
                "message": "Missing 'campaign_name'"
            }), 400

        # 🔥 Call your bulk function
        updated = scrape_social_post_instagram(campaign_name)

        return jsonify({
            "status": "success",
            "campaign_name": campaign_name,
            "updated_records": updated
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# http://127.0.0.1:5050/update-analytics-post?campaign_name=AJIO-Qatar-Fashion-Apparel-02
@app.route("/update-analytics-post", methods=["GET", "POST"])
def update_analytics_post():
    try:
        campaign_name = request.args.get("campaign_name")
        if not campaign_name:
            return jsonify({
                "status": "error",
                "message": "campaign_name is required"
            }), 400

        updated_records = scrape_social_post_for_all(campaign_name)

        return jsonify({
            "status": "success",
            "updated_records": updated_records,
            "campaign_name": campaign_name
        }), 200

    except Exception as e:
        print("❌ Error in update_analytics_post:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# @app.route('/upload-instagram-pics', methods=['GET'])
# def upload_instagram_pics_get():
#     table_name = request.args.get("table_name")
#     target_fields = request.args.get(
#         "target_fields",
#         "saved_profile_pic,downloadable_profile_pic"
#     ).split(",")

#     if not table_name:
#         return jsonify({"status": "failed", "message": "Missing table_name"}), 400

#     airtable = Table(
#         AIRTABLE_API_KEY,
#         AIRTABLE_BASE_ID,
#         table_name,
#         timeout=30
#     )

#     skipped_no_handle = []
#     skipped_already_exists = []
#     failed_updates = []
#     updated_records = 0

#     try:
#         records = airtable.all()

#         for record in records:
#             record_id = record["id"]
#             fields = record.get("fields", {})

#             username = fields.get("instagram_username")
#             if not username:
#                 skipped_no_handle.append(record_id)
#                 continue

#             if fields.get("downloadable_profile_pic"):
#                 skipped_already_exists.append(record_id)
#                 continue

#             profile_data = profile_scraper(username)
#             if not profile_data:
#                 failed_updates.append(record_id)
#                 continue

#             profile_pic = profile_data.get("instagram_profile_pic")
#             if not profile_pic:
#                 failed_updates.append(record_id)
#                 continue

#             drive_url, err = process_and_upload_image_with_airtable(profile_pic)
#             if err or not drive_url:
#                 failed_updates.append(record_id)
#                 continue

#             update_data = {
#                 target_fields[0]: [{"url": drive_url}],
#                 target_fields[1]: drive_url
#             }

#             success = safe_airtable_update(airtable, record_id, update_data)
#             if success:
#                 updated_records += 1
#                 print(f"Updated record {record_id}")
#             else:
#                 failed_updates.append(record_id)

#             # ⛔ Airtable rate limit protection
#             time.sleep(0.5)

#         return jsonify({
#             "status": "success",
#             "updated_records": updated_records,
#             "skipped_no_handle": skipped_no_handle,
#             "skipped_already_exists": skipped_already_exists,
#             "failed_updates": failed_updates
#         }), 200

#     except Exception as e:
#         traceback.print_exc()
#         return jsonify({"status": "failed", "message": str(e)}), 500


@app.route("/update_influencers_by_date", methods=["GET"])
def update_influencers_by_date():
    try:
        target_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "influencers_instagram_registered")
        target_records = target_table.all()

        # Target date to check (YYYY-MM-DD)
        target_date = "2026-01-13"

        for rec in target_records:
            fields = rec.get("fields", {})
            instagram_handle = fields.get("instagram_username")
            last_scraped = fields.get("last_scraped_at")

            if not instagram_handle or not last_scraped:
                continue

            normalized_handle = instagram_handle.strip().lstrip("@")

            # ---- Check if last_scraped_at date matches target_date ----
            try:
                last_scraped_date = last_scraped.split("T")[0]  # Extract date part only
            except:
                last_scraped_date = last_scraped[:10]  # Fallback: take first 10 chars

            if last_scraped_date != target_date:
                continue  # Skip if date doesn't match

            print(f"🔄 Updating {normalized_handle} (last_scraped_at date = {target_date})...")

            # ---- PROFILE SCRAPER ----
            try:
                profile_data = profile_scraper(
                    normalized_handle,
                    influencer_type=fields.get("brands_collaborated"),
                    influencer_location=fields.get("influencer_location")
                ) or {}
            except Exception as e:
                print(f"Profile error for {normalized_handle}: {e}")
                continue

            # ---- POST SCRAPER ----
            try:
                followers_count = profile_data.get("instagram_followers_count") or 1
                post_data = post_scraper(
                    normalized_handle,
                    posts_count=5,
                    followers_count=int(followers_count)
                ) or {}
            except Exception as e:
                print(f"Post error for {normalized_handle}: {e}")
                post_data = {}

            # ---- ENGAGEMENT RATE ----
            try:
                engagement_info = asyncio.get_event_loop().run_until_complete(
                    get_engagement_rate([normalized_handle])
                )
                engagement_rate = engagement_info[0].get("engagement_rate_pct", 0) if engagement_info else 0
            except Exception as e:
                print(f"Engagement fetch failed for {normalized_handle}: {e}")
                engagement_rate = 0

            # ---- BUILD UPDATE DATA ----
            update_data = {
                "instagram_bio": str(profile_data.get("instagram_bio", "")),
                "instagram_profile_pic": str(profile_data.get("instagram_profile_pic", "")),
                "instagram_followers_count": str(profile_data.get("instagram_followers_count", "")),
                "instagram_follows_count": str(profile_data.get("instagram_follows_count", "")),
                "instagram_posts_count": str(profile_data.get("instagram_posts_count", "")),
                "instagram_comments_counts": str(post_data.get("instagram_comments_counts", "")),
                "instagram_likes_counts": str(post_data.get("instagram_likes_counts", "")),
                "instagram_video_play_counts": str(post_data.get("instagram_video_play_counts", "")),
                "instagram_video_urls": str(post_data.get("instagram_video_urls", "")),
                "avg_likes": str(post_data.get("avg_likes", "")),
                "avg_comments": str(post_data.get("avg_comments", "")),
                "avg_video_play_counts": str(post_data.get("avg_video_play_counts", "")),
                "videos_engagement": str(post_data.get("estimated_reach", "")),
                "engagement_rate": str(engagement_rate),
                "last_scraped_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Update record
            record_id = rec.get("id")
            if record_id:
                target_table.update(record_id, update_data)
                print(f"✅ Updated {normalized_handle} → {record_id}")

        return jsonify({"status": "success", "message": f"Updated all records with last_scraped_at date = {target_date}."})

    except Exception as e:
        print(f"❌ Error in pipeline: {e}")
        return jsonify({"status": "failed", "error": str(e)})

@app.route("/engagement_rate", methods=["POST"])
def engagement_rate_endpoint():
    data = request.get_json()
    usernames = data.get("usernames", [])
    if not usernames:
        return jsonify({"status": "failed", "error": "No usernames provided"}), 400

    engagement_data = asyncio.get_event_loop().run_until_complete(get_engagement_rate(usernames))
    return jsonify({"status": "passed", "data": engagement_data})

def safe_long_text(value):
    """Convert None or list to string safely for Airtable long text fields."""
    if value is None:
        return ""
    elif isinstance(value, list):
        # Join list of dicts or strings into comma-separated string
        new_list = []
        for v in value:
            if isinstance(v, dict):
                # Try to use 'url' or 'lynx_url' if available
                new_list.append(v.get("url") or v.get("lynx_url") or str(v))
            else:
                new_list.append(str(v))
        return ", ".join(new_list)
    return str(value)

from datetime import datetime

# @app.route("/update_registered_influencers", methods=["GET"])
# def update_registered_influencers():
#     try:
#         target_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "influencers_instagram_registered")

#         target_records = target_table.all()
#         existing_map = {rec['fields'].get('instagram_username'): rec['id'] for rec in target_records}

#         for rec in target_records:
#             fields = rec.get("fields", {})
#             instagram_handle = fields.get("instagram_username")
#             if not instagram_handle:
#                 continue

#             normalized_handle = instagram_handle.strip().lstrip("@")
#             if not normalized_handle:
#                 continue

#             print(f"🔄 Updating {normalized_handle}...")

#             # ---- PROFILE SCRAPER ----
#             try:
#                 profile_data = profile_scraper(
#                     normalized_handle,
#                     influencer_type=fields.get("brands_collaborated"),
#                     influencer_location=fields.get("influencer_location")
#                 ) or {}
#             except Exception as e:
#                 print(f"Profile error for {normalized_handle}: {e}")
#                 continue

#             # ---- POST SCRAPER ----
#             try:
#                 followers_count = profile_data.get("instagram_followers_count") or 1
#                 post_data = post_scraper(
#                     normalized_handle,
#                     posts_count=5,
#                     followers_count=int(followers_count)
#                 ) or {}
#             except Exception as e:
#                 print(f"Post error for {normalized_handle}: {e}")
#                 post_data = {}

#             # ---- ENGAGEMENT RATE ----
#             try:
#                 engagement_info = asyncio.get_event_loop().run_until_complete(
#                     get_engagement_rate([normalized_handle])
#                 )
#                 engagement_rate = engagement_info[0].get("engagement_rate_pct", 0) if engagement_info else 0
#             except Exception as e:
#                 print(f"Engagement fetch failed for {normalized_handle}: {e}")
#                 engagement_rate = 0

#             # ---- BUILD UPDATE DATA ----
#             update_data = {
#                 # Profile Info
#                 "instagram_bio": str(profile_data.get("instagram_bio", "")),
#                 "instagram_profile_pic": str(profile_data.get("instagram_profile_pic", "")),
#                 "instagram_followers_count": str(profile_data.get("instagram_followers_count", "")),
#                 "instagram_follows_count": str(profile_data.get("instagram_follows_count", "")),
#                 "instagram_posts_count": str(profile_data.get("instagram_posts_count", "")),

#                 # Post Info
#                 "instagram_comments_counts": str(post_data.get("instagram_comments_counts", "")),
#                 "instagram_likes_counts": str(post_data.get("instagram_likes_counts", "")),
#                 "instagram_video_play_counts": str(post_data.get("instagram_video_play_counts", "")),
#                 "instagram_video_urls": str(post_data.get("instagram_video_urls", "")),
#                 "avg_likes": str(post_data.get("avg_likes", "")),
#                 "avg_comments": str(post_data.get("avg_comments", "")),
#                 "avg_video_play_counts": str(post_data.get("avg_video_play_counts", "")),
#                 "videos_engagement": str(post_data.get("estimated_reach", "")),

#                 # Engagement Rate
#                 "engagement_rate": str(engagement_rate),

#                 # Timestamp for last scrape
#                 "last_scraped_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")  # UTC timestamp
#             }

#             # Update existing record
#             record_id = existing_map.get(normalized_handle)
#             if record_id:
#                 target_table.update(record_id, update_data)
#                 print(f"✅ Updated {normalized_handle} → {record_id}")

#         return {"status": "success", "message": "Weekly update pipeline executed successfully."}

#     except Exception as e:
#         print(f"❌ Error in pipeline: {e}")
#         return {"status": "failed", "error": str(e)}
LOCAL_TZ = pytz.timezone("Asia/Dubai")
@app.route('/upload-instagram-pics', methods=['GET'])
def upload_instagram_pics_get():

    table_name = request.args.get("table_name")
    target_fields = request.args.get(
        "target_fields",
        "saved_profile_pic,downloadable_profile_pic"
    ).split(",")

    if not table_name:
        return jsonify({
            "status": "failed",
            "message": "Missing table_name"
        }), 400

    try:
        # ✅ Updated pyairtable usage (no deprecation warning)
        api = Api(AIRTABLE_API_KEY)
        airtable = api.table(AIRTABLE_BASE_ID, table_name)

        skipped_no_handle = []
        skipped_already_exists = []
        updated_records = 0

        records = airtable.all(sort=["-created_time"])

        for record in records:

            record_id = record.get("id")
            fields = record.get("fields", {})

            normalized_handle = fields.get("instagram_username")

            if not normalized_handle:
                skipped_no_handle.append(record_id)
                continue

            downloadable = fields.get("downloadable_profile_pic")

            if downloadable not in (None, [], ""):
                skipped_already_exists.append(record_id)
                continue

            # ✅ Proper async execution inside sync route
            try:
                profile_data = asyncio.run(
                    profile_scraper([normalized_handle])
                )
            except Exception as e:
                print(f"Error in profile_scraper for record {record_id}: {e}")
                continue

            if not profile_data:
                print(f"Skipping record {record_id}, empty profile data")
                continue

            first_profile = profile_data[0]
            new_profile_pic = first_profile.get("instagram_profile_pic")

            if not new_profile_pic:
                print(f"Skipping record {record_id}, no profile pic found")
                continue

            # Upload image to Google Drive
            drive_url, err = process_and_upload_image_with_airtable(
                new_profile_pic
            )

            if err:
                print(f"Drive upload failed for record {record_id}: {err}")
                continue

            # Current Dubai time
            now_dubai = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")

            update_data = {
                target_fields[0]: [{"url": drive_url}],
                target_fields[1]: drive_url,
                # "profile_pic_uploaded_at": now_dubai
            }

            try:
                airtable.update(record_id, update_data)
                updated_records += 1
                print(f"Updated record {record_id}")
            except Exception as e:
                print(f"Airtable update failed for {record_id}: {e}")
                continue

        print("Skipped (no handle):", skipped_no_handle)
        print("Skipped (already exists):", skipped_already_exists)

        return jsonify({
            "status": "success",
            "updated_records": updated_records,
            "skipped_no_handle": skipped_no_handle,
            "skipped_already_exists": skipped_already_exists
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "failed",
            "message": str(e)
        }), 500
    
@app.route("/update_registered_influencers", methods=["GET"])
def update_registered_influencers():
    try:
        target_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "influencers_instagram_registered")

        # Fetch all existing records
        target_records = target_table.all()
        existing_map = {rec['fields'].get('instagram_username'): rec['id'] for rec in target_records}

        for rec in target_records:
            fields = rec.get("fields", {})
            instagram_handle = fields.get("instagram_username")
            if not instagram_handle:
                continue

            normalized_handle = instagram_handle.strip().lstrip("@")
            if not normalized_handle:
                continue

            # ---- Check last_scraped_at (7-day rule) ----
            last_scraped = fields.get("last_scraped_at")
            update_needed = True
            if last_scraped:
                try:
                    last_scraped_dt = datetime.strptime(last_scraped, "%Y-%m-%d %H:%M:%S")
                    last_scraped_dt = pytz.utc.localize(last_scraped_dt).astimezone(LOCAL_TZ)
                    if datetime.now(LOCAL_TZ) - last_scraped_dt < timedelta(days=7):
                        update_needed = False
                except Exception as e:
                    print(f"⚠ Could not parse last_scraped_at for {normalized_handle}: {e}")

            if not update_needed:
                print(f"⏭ Skipping {normalized_handle}, updated less than 7 days ago.")
                continue

            print(f"🔄 Updating {normalized_handle}...")

            # ---- PROFILE SCRAPER ----
            try:
                profile_data = profile_scraper(
                    normalized_handle,
                    influencer_type=fields.get("brands_collaborated"),
                    influencer_location=fields.get("influencer_location")
                ) or {}
            except Exception as e:
                print(f"Profile error for {normalized_handle}: {e}")
                continue

            # ---- POST SCRAPER ----
            try:
                followers_count = profile_data.get("instagram_followers_count") or 1
                post_data = post_scraper(
                    normalized_handle,
                    posts_count=5,
                    followers_count=int(followers_count)
                ) or {}
            except Exception as e:
                print(f"Post error for {normalized_handle}: {e}")
                post_data = {}

            # ---- ENGAGEMENT RATE ----
            try:
                engagement_info = asyncio.get_event_loop().run_until_complete(
                    get_engagement_rate([normalized_handle])
                )
                engagement_rate = engagement_info[0].get("engagement_rate_pct", 0) if engagement_info else 0
            except Exception as e:
                print(f"Engagement fetch failed for {normalized_handle}: {e}")
                engagement_rate = 0

            # ---- BUILD UPDATE DATA ----
            update_data = {
                # Profile Info
                "instagram_bio": str(profile_data.get("instagram_bio", "")),
                "instagram_profile_pic": str(profile_data.get("instagram_profile_pic", "")),
                "instagram_followers_count": str(profile_data.get("instagram_followers_count", "")),
                "instagram_follows_count": str(profile_data.get("instagram_follows_count", "")),
                "instagram_posts_count": str(profile_data.get("instagram_posts_count", "")),

                # Post Info
                "instagram_comments_counts": str(post_data.get("instagram_comments_counts", "")),
                "instagram_likes_counts": str(post_data.get("instagram_likes_counts", "")),
                "instagram_video_play_counts": str(post_data.get("instagram_video_play_counts", "")),
                "instagram_video_urls": str(post_data.get("instagram_video_urls", "")),
                "avg_likes": str(post_data.get("avg_likes", "")),
                "avg_comments": str(post_data.get("avg_comments", "")),
                "avg_video_play_counts": str(post_data.get("avg_video_play_counts", "")),
                "videos_engagement": str(post_data.get("estimated_reach", "")),

                # Engagement Rate
                "engagement_rate": str(engagement_rate),

                # Timestamp for last scrape (local time)
                "last_scraped_at": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
            }

            # Update existing record
            record_id = existing_map.get(normalized_handle)
            if record_id:
                target_table.update(record_id, update_data)
                print(f"✅ Updated {normalized_handle} → {record_id}")

        return jsonify({"status": "success", "message": "Weekly update pipeline executed successfully."})

    except Exception as e:
        print(f"❌ Error in pipeline: {e}")
        return jsonify({"status": "failed", "error": str(e)})


# ------------------ REGISTERED INFLUENCERS PIPELINE ------------------
# @app.route("/registered_influencers_pipeline", methods=["GET"])
# def registered_influencers_pipeline_v2():
#     try:
#         source_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "registered_influencers_v3")
#         target_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "influencers_instagram_registered")

#         source_records = source_table.all()

#         for record in source_records:
#             fields = record.get("fields", {})
#             instagram_handle = fields.get("instagram_handle_name")
#             if not instagram_handle:
#                 continue

#             normalized_handle = instagram_handle.strip().lstrip("@")
#             if not normalized_handle:
#                 continue

#             # Skip if already exists
#             existing = target_table.all(formula=f"{{instagram_username}}='{normalized_handle}'")
#             if existing:
#                 print(f"Skipping {normalized_handle}, already exists.")
#                 continue

#             print(f"🚀 Starting pipeline for {normalized_handle}...")

#             # ---- PROFILE SCRAPER ----
#             try:
#                 profile_data = profile_scraper(
#                     normalized_handle,
#                     influencer_type=fields.get("brands_collaborated"),
#                     influencer_location=fields.get("country")
#                 ) or {}
#             except Exception as e:
#                 print(f"❌ Profile error for {normalized_handle}: {e}")
#                 continue

#             # ---- POST SCRAPER ----
#             try:
#                 followers_count = int(profile_data.get("instagram_followers_count") or 1)
#                 post_data = post_scraper(
#                     normalized_handle,
#                     posts_count=5,
#                     followers_count=followers_count
#                 ) or {}
#             except Exception as e:
#                 print(f"❌ Post error for {normalized_handle}: {e}")
#                 post_data = {}

#             # ---- ENGAGEMENT RATE (ASYNC) ----
#             try:
#                 engagement_info = asyncio.get_event_loop().run_until_complete(
#                     get_engagement_rate([normalized_handle])
#                 )

#                 if engagement_info:
#                     engagement_item = engagement_info[0]
#                     engagement_rate = engagement_item.get("engagement_rate", 0)
#                     avg_likes = engagement_item.get("average_likes", "")
#                     avg_comments = engagement_item.get("average_comments", "")
#                     avg_views = engagement_item.get("average_views", "")
#                 else:
#                     engagement_rate = 0
#                     avg_likes = avg_comments = avg_views = ""

#             except Exception as e:
#                 print(f"❌ Engagement fetch failed for {normalized_handle}: {e}")
#                 engagement_rate = 0
#                 avg_likes = avg_comments = avg_views = ""

#             # ---- BUILD OUTPUT RECORD ----
#             combined_data = {}

#             # --- PROFILE FIELDS ---
#             combined_data.update({
#                 "instagram_url": str(profile_data.get("instagram_url", "")),
#                 "instagram_username": str(normalized_handle),
#                 "full_name": str(profile_data.get("full_name", "")),
#                 "instagram_bio": str(profile_data.get("instagram_bio", "")),
#                 "external_urls": str(profile_data.get("external_urls", "")),
#                 "instagram_followers_count": str(profile_data.get("instagram_followers_count", "")),
#                 "instagram_follows_count": str(profile_data.get("instagram_follows_count", "")),
#                 "business_category_name": str(profile_data.get("business_category_name", "")),
#                 "instagram_profile_pic": str(profile_data.get("instagram_profile_pic", "")),
#                 "instagram_posts_count": str(profile_data.get("instagram_posts_count", "")),
#                 "influencer_location": str(profile_data.get("influencer_location", "")),
#                 "influencer_nationality": str(fields.get("nationality", "")),
#             })

#             # --- POST FIELDS ---
#             combined_data.update({
#                 "instagram_captions": str(post_data.get("instagram_captions", "")),
#                 "instagram_hashtags": str(post_data.get("instagram_hashtags", "")),
#                 "instagram_post_urls": str(post_data.get("instagram_post_urls", "")),
#                 "instagram_comments_counts": str(post_data.get("instagram_comments_counts", "")),
#                 "instagram_likes_counts": str(post_data.get("instagram_likes_counts", "")),
#                 "instagram_video_urls": str(post_data.get("instagram_video_urls", "")),
#                 "instagram_video_play_counts": str(post_data.get("instagram_video_play_counts", "")),
#                 "avg_likes": str(avg_likes),
#                 "avg_comments": str(avg_comments),
#                 "avg_video_play_counts": str(avg_views),
#                 "engagement_rate": str(engagement_rate),
#                 "videos_engagement": str(post_data.get("estimated_reach", "")),
#             })

#             # --- SOURCE FIELDS ---
#             combined_data.update({
#                 "brands_collaborated": str(fields.get("brands_collaborated", "")),
#                 "countries_in_bio": str(fields.get("country", "")),
#                 "email_id": str(fields.get("email", "")),
#                 "facebook_id": str(fields.get("fb_handle_name", "")),
#                 "cities_in_bio": str(fields.get("location", "")),
#                 "influencer_nationality": str(fields.get("nationality", "")),
#                 "phone": str(fields.get("phone_number", "")),
#                 "snapchat_id": str(fields.get("snap_handle_name", "")),
#                 "tiktok_url": str(fields.get("tiktok_handle_name", "")),
#                 "twitter_id": str(fields.get("twitter_handle_name", "")),
#             })

#             # ---- INSERT RECORD ----
#             response = target_table.create(combined_data)
#             print(f"✅ Inserted {normalized_handle} → {response['id']}")

#         return jsonify({"status": "passed", "message": "Pipeline executed successfully"})

#     except Exception as e:
#         print(f"❌ Error in pipeline: {e}")
#         return jsonify({"status": "failed", "error": str(e)})


@app.route("/registered_influencers_pipeline", methods=["GET"])
def registered_influencers_pipeline_v2():
    try:
        source_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "registered_influencers_v3")
        target_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "influencers_instagram_registered")

        source_records = source_table.all()

        for record in source_records:
            fields = record.get("fields", {})
            instagram_handle = fields.get("instagram_handle_name")

            if not instagram_handle:
                continue

            normalized_handle = instagram_handle.strip().lstrip("@")
            if not normalized_handle:
                continue

            existing = target_table.all(formula=f"{{instagram_username}}='{normalized_handle}'")
            if existing:
                print(f"Skipping {normalized_handle}, already exists.")
                continue

            print(f"🚀 Starting pipeline for {normalized_handle}...")

            # ---- PROFILE SCRAPER ----
            profile_results = asyncio.get_event_loop().run_until_complete(
                profile_scraper([normalized_handle])
            )

            if not profile_results:
                print(f"No profile data for {normalized_handle}")
                continue

            profile_data = profile_results[0]   # because it returns a list

            # ---- POST SCRAPER ----
            try:
                followers_count = profile_data.get("instagram_followers_count") or 1
                post_data = post_scraper(
                    normalized_handle,
                    posts_count=5,
                    followers_count=int(followers_count)
                ) or {}
                
            except Exception as e:
                print(f"Post error for {normalized_handle}: {e}")
                post_data = {}

            # ---- ENGAGEMENT RATE (ASYNC) ----
            # try:
            #     engagement_info = asyncio.get_event_loop().run_until_complete(
            #         get_engagement_rate([normalized_handle])
            #     )
            #     engagement_rate = engagement_info[0].get("engagement_rate_pct", 0) if engagement_info else 0
            # except Exception as e:
            #     print(f"Engagement fetch failed for {normalized_handle}: {e}")
            #     engagement_rate = 0

            # post_data["engagement_rate"] = engagement_rate
            # try:
            #     engagement_info = asyncio.get_event_loop().run_until_complete(
            #         get_engagement_rate([normalized_handle])
            #     )

            #     if engagement_info:
            #         engagement_item = engagement_info[0]
            #         engagement_rate = engagement_item.get("engagement_rate", 0)
            #         avg_likes = engagement_item.get("average_likes", "")
            #         avg_comments = engagement_item.get("average_comments", "")
            #         avg_views = engagement_item.get("average_views", "")
            #     else:
            #         engagement_rate = 0
            #         avg_likes = avg_comments = avg_views = ""

            # except Exception as e:
            #     print(f"❌ Engagement fetch failed for {normalized_handle}: {e}")
            #     engagement_rate = 0
            #     avg_likes = avg_comments = avg_views = ""

            # ---- BUILD OUTPUT RECORD ----
            combined_data = {}

            # --- PROFILE FIELDS ---
            combined_data.update({
                "instagram_url": str(profile_data.get("instagram_url", "")),
                "instagram_username": str(normalized_handle),
                # "full_name": str(profile_data.get("full_name", "")),
                "instagram_bio": str(profile_data.get("instagram_bio", "")),
                "external_urls": str(profile_data.get("external_urls", "")),
                "instagram_followers_count": str(profile_data.get("instagram_followers_count", "")),
                "instagram_follows_count": str(profile_data.get("instagram_follows_count", "")),
                "business_category_name": str(profile_data.get("business_category_name", "")),
                "instagram_profile_pic": str(profile_data.get("instagram_profile_pic", "")),
                "instagram_posts_count": str(profile_data.get("instagram_posts_count", "")),
                "influencer_location": str(profile_data.get("influencer_location", "")),
                
                "avg_likes": str(profile_data.get("average_likes", "")),
                "avg_comments": str(profile_data.get("average_comments", "")),
                "avg_video_play_counts": str(profile_data.get("average_views", "")),
                "engagement_rate": str(profile_data.get("engagement_rate_percent", "")),
                "videos_engagement": str(profile_data.get("average_views", "")),
                "influencer_nationality": str(fields.get("nationality", "")),
            })

            # --- POST FIELDS ---
            combined_data.update({
                "instagram_captions": str(post_data.get("instagram_captions", "")),
                "instagram_hashtags": str(post_data.get("instagram_hashtags", "")),
                "instagram_post_urls": str(post_data.get("instagram_post_urls", "")),
                "instagram_comments_counts": str(post_data.get("instagram_comments_counts", "")),
                "instagram_likes_counts": str(post_data.get("instagram_likes_counts", "")),
                "instagram_video_urls": str(post_data.get("instagram_video_urls", "")),
                "instagram_video_play_counts": str(post_data.get("instagram_video_play_counts", "")),
                # "avg_comments": str(post_data.get("avg_comments", "")),
                # "avg_likes": str(post_data.get("avg_likes", "")),
                # "avg_video_play_counts": str(post_data.get("avg_video_play_counts", "")),
                # "avg_likes": str(avg_likes),
                # "avg_comments": str(avg_comments),
                # "avg_video_play_counts": str(avg_views),
                # "engagement_rate": str(engagement_rate),
                # "videos_engagement": str(avg_views),
                # "engagement_rate": str(post_data.get("engagement_rate", "")),
                # "videos_engagement": str(post_data.get("estimated_reach", "")),
            })

            # --- SOURCE FIELDS ---
            combined_data.update({
                "brands_collaborated": str(fields.get("brands_collaborated", "")),
                "countries_in_bio": str(fields.get("country", "")),
                "email_id": str(fields.get("email", "")),
                "facebook_id": str(fields.get("fb_handle_name", "")),
                "cities_in_bio": str(fields.get("location", "")),
                "influencer_nationality": str(fields.get("nationality", "")),
                "phone": str(fields.get("phone_number", "")),
                "snapchat_id": str(fields.get("snap_handle_name", "")),
                "tiktok_id": str(fields.get("tiktok_handle_name", "")),
                "twitter_id": str(fields.get("twitter_handle_name", "")),
                "full_name": str(fields.get("first_name", "")),
            })

            response = target_table.create(combined_data)
            print(f"✅ Inserted {normalized_handle} → {response['id']}")

        return {"status": "passed", "message": "Pipeline executed successfully"}

    except Exception as e:
        print(f"❌ Error in pipeline: {e}")
        return {"status": "failed", "error": str(e)}

    
# @app.route("/registered_influencers_pipeline", methods=["GET"]) 
# def registered_influencers_pipeline_v2():
#     try:
#         # Source and target tables
#         source_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "registered_influencers_v3")
#         target_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "influencers_instagram_registered")

#         source_records = source_table.all()

#         for record in source_records:
#             fields = record.get("fields", {})
#             instagram_handle = fields.get("instagram_handle_name")  

#             if not instagram_handle:
#                 continue

#             # --- Normalize handle (remove '@' and trim spaces) ---
#             normalized_handle = instagram_handle.strip().lstrip("@")

#             if not normalized_handle:
#                 continue

#             # --- Check if already exists in target ---
#             existing = target_table.all(formula=f"{{instagram_username}}='{normalized_handle}'")
#             if existing:
#                 print(f"Skipping {normalized_handle}, already exists.")
#                 continue

#             print(f"Starting pipeline for {normalized_handle}...")

#             # Run scrapers with error handling
#             try:
#                 profile_data = profile_scraper(
#                     normalized_handle,
#                     influencer_type=fields.get("brands_collaborated"),
#                     influencer_location=fields.get("country")
#                 ) or {}   # ensure dict even if None
#             except Exception as e:
#                 print(f"Error in profile scraper for {normalized_handle}: {e}")
#                 continue  # skip this influencer

#             try:
#                 post_data = post_scraper(
#                     normalized_handle,
#                     posts_count=5,
#                     followers_count=int(profile_data.get("instagram_followers_count", 1) or 1)
#                 ) or {}
#             except Exception as e:
#                 print(f"Error in post scraper for {normalized_handle}: {e}")
#                 post_data = {}

#             # Call async engagement_rate
#             engagement_info = asyncio.get_event_loop().run_until_complete(
#                 get_engagement_rate([normalized_handle])
#             )
#             engagement_rate = engagement_info[0]['engagement_rate_pct'] if engagement_info else 0
#             post_data["engagement_rate"] = engagement_rate

#             # Build normalized record
#             combined_data = {}

#             # Profile data mapping
#             profile_mapping = {
#                 "instagram_url": str(profile_data.get("instagram_url", "")),
#                 "instagram_username": str(normalized_handle),  # store normalized
#                 "full_name": str(profile_data.get("full_name", "")),
#                 "instagram_bio": str(profile_data.get("instagram_bio", "")),
#                 "external_urls": str(profile_data.get("external_urls", "")),
#                 "instagram_followers_count": str(profile_data.get("instagram_followers_count", "")),
#                 "instagram_follows_count": str(profile_data.get("instagram_follows_count", "")),
#                 "business_category_name": str(profile_data.get("business_category_name", "")),
#                 "instagram_profile_pic": str(profile_data.get("instagram_profile_pic", "")),
#                 "instagram_posts_count": str(profile_data.get("instagram_posts_count", "")),
#                 "influencer_location": str(profile_data.get("influencer_location", "")),
#                 "influencer_nationality": str(fields.get("nationality", "")),
#                 # "niche_en": str(fields.get("brands_collaborated", "")),
#             }
#             combined_data.update(profile_mapping)

#             # Post data mapping
#             post_mapping = {
#                 "instagram_captions": str(post_data.get("instagram_captions", "")),
#                 "instagram_hashtags": str(post_data.get("instagram_hashtags", "")),
#                 "instagram_post_urls": str(post_data.get("instagram_post_urls", "")),
#                 "instagram_comments_counts": str(post_data.get("instagram_comments_counts", "")),
#                 "instagram_video_play_counts": str(post_data.get("instagram_video_play_counts", "")),
#                 "instagram_video_urls": str(post_data.get("instagram_video_urls", "")),
#                 "instagram_likes_counts": str(post_data.get("instagram_likes_counts", "")),
#                 "avg_comments": str(post_data.get("avg_comments", "")),
#                 "avg_likes": str(post_data.get("avg_likes", "")),
#                 "avg_video_play_counts": str(post_data.get("avg_video_play_counts", "")),
#                 "engagement_rate": str(post_data.get("engagement_rate", "")),
#                 "videos_engagement": str(post_data.get("estimated_reach", "")),
#             }
#             combined_data.update(post_mapping)

#             # Source fields mapping
#             source_mapping = {
#                 "brands_collaborated": str(fields.get("brands_collaborated", "")),
#                 "countries_in_bio": str(fields.get("country", "")),
#                 # "created_time": str(fields.get("created_time", "")),
#                 "email_id": str(fields.get("email", "")),
#                 "facebook_id": str(fields.get("fb_handle_name", "")),
#                 "full_name": str(fields.get("first_name", "")),
#                 # "instagram_username": str(instagram_handle),  # keep original with @ if exists
#                 "cities_in_bio": str(fields.get("location", "")),
#                 "influencer_nationality": str(fields.get("nationality", "")),
#                 "phone": str(fields.get("phone_number", "")),
#                 "snapchat_id": str(fields.get("snap_handle_name", "")),
#                 "tiktok_url": str(fields.get("tiktok_handle_name", "")),
#                 "twitter_id": str(fields.get("twitter_handle_name", "")),
#             }
#             combined_data.update(source_mapping)

#             # Insert into Airtable
#             response = target_table.create(combined_data)
#             print(f"Inserted {normalized_handle} → {response['id']}")

#         return {"status": "passed", "message": "Pipeline executed successfully"}

#     except Exception as e:
#         print(f"Error in registered_influencers_pipeline_v2: {e}")
#         return {"status": "failed", "error": str(e)}


# @app.route("/influencer_data_pipeline", methods=["GET"])
# def influencer_data_pipeline():
#     try:
#         source_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "taippa_influencer_v3_source")
#         target_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "influencers_instagram_v3")

#         source_records = source_table.all()

#         for record in source_records:
#             fields = record.get("fields", {})
#             instagram_handle = fields.get("instagram_handle")

#             if not instagram_handle:
#                 continue

#             # Check if already exists in target
#             existing = target_table.all(formula=f"{{instagram_username}}='{instagram_handle}'")
#             if existing:
#                 print(f"Skipping {instagram_handle}, already exists.")
#                 continue

#             print(f"🚀 Starting pipeline for {instagram_handle}...")

#             # Run profile scraper
#             profile_data = profile_scraper(
#                 instagram_handle,
#                 fields.get("niche"),
#                 fields.get("primary_location_country")
#             )
#             if not profile_data or not isinstance(profile_data, dict):
#                 print(f"⚠️ Profile scraper failed for {instagram_handle}, skipping...")
#                 continue

#             # Run post scraper
#             followers_count = profile_data.get("instagram_followers_count") or 1
#             post_data = post_scraper(instagram_handle, posts_count=5, followers_count=followers_count)
#             if not post_data or not isinstance(post_data, dict):
#                 print(f"⚠️ Post scraper failed for {instagram_handle}, skipping...")
#                 continue

#             # Engagement rate fetch
#             try:
#                 engagement_info = asyncio.get_event_loop().run_until_complete(
#                     get_engagement_rate([instagram_handle])
#                 )
#                 engagement_rate = (
#                     engagement_info[0].get("engagement_rate_pct", 0)
#                     if engagement_info and isinstance(engagement_info, list)
#                     else 0
#                 )
#             except Exception as e:
#                 print(f"⚠️ Engagement rate fetch failed for {instagram_handle}: {e}")
#                 engagement_rate = 0

#             post_data["engagement_rate"] = engagement_rate  # overwrite or update

#             # Build normalized record with all values as strings
#             combined_data = {}

#             # Profile data mapping
#             profile_mapping = {
#                 "instagram_url": str(profile_data.get("instagram_url", "")),
#                 "instagram_username": str(profile_data.get("instagram_username", "")),
#                 "full_name": str(profile_data.get("full_name", "")),
#                 "instagram_bio": str(profile_data.get("instagram_bio", "")),
#                 "external_urls": str(profile_data.get("external_urls", "")),
#                 "instagram_followers_count": str(profile_data.get("instagram_followers_count", "")),
#                 "instagram_follows_count": str(profile_data.get("instagram_follows_count", "")),
#                 "business_category_name": str(profile_data.get("business_category_name", "")),
#                 "instagram_profile_pic": str(profile_data.get("instagram_profile_pic", "")),
#                 "instagram_posts_count": str(profile_data.get("instagram_posts_count", "")),
#                 "influencer_type": str(profile_data.get("influencer_type", "")),
#                 "influencer_location": str(profile_data.get("influencer_location", "")),
#             }
#             combined_data.update(profile_mapping)

#             # Post data mapping
#             post_mapping = {
#                 "instagram_captions": str(post_data.get("instagram_captions", "")),
#                 "instagram_hashtags": str(post_data.get("instagram_hashtags", "")),
#                 "instagram_post_urls": str(post_data.get("instagram_post_urls", "")),
#                 "instagram_comments_counts": str(post_data.get("instagram_comments_counts", "")),
#                 "instagram_video_play_counts": str(post_data.get("instagram_video_play_counts", "")),
#                 "instagram_video_urls": str(post_data.get("instagram_video_urls", "")),
#                 "instagram_likes_counts": str(post_data.get("instagram_likes_counts", "")),
#                 "avg_comments": str(post_data.get("avg_comments", "")),
#                 "avg_likes": str(post_data.get("avg_likes", "")),
#                 "avg_video_play_counts": str(post_data.get("avg_video_play_counts", "")),
#                 "engagement_rate": str(post_data.get("engagement_rate", "")),  # updated
#                 "videos_engagement": str(post_data.get("estimated_reach", "")),
#             }
#             combined_data.update(post_mapping)

#             # Source fields mapping
#             source_mapping = {
#                 "full_name": str(fields.get("full_name", "")),
#                 "niche_en": str(fields.get("niche", "")),
#                 "influencer_tier": str(fields.get("influencer_tier", "")),
#                 "gender": str(fields.get("gender", "")),
#                 "top_interest": str(fields.get("top_interest", "")),
#                 "phone": str(fields.get("phone", "")),
#                 "email_id": str(fields.get("email_id", "")),
#                 "cities_in_bio": str(fields.get("primary_loaction_city", "")),
#                 "countries_in_bio": str(fields.get("primary_location_country", "")),
#                 "preferred_contact_method": str(fields.get("preferred_contact_method", "")),
#             }
#             combined_data.update(source_mapping)

#             # Insert into Airtable
#             try:
#                 response = target_table.create(combined_data)
#                 print(f"✅ Inserted {instagram_handle} → {response['id']}")
#             except Exception as e:
#                 print(f"❌ Failed to insert {instagram_handle}: {e}")

#         return {"status": "passed", "message": "Pipeline executed successfully"}

#     except Exception as e:
#         print(f"❌ Error in influencer_data_pipeline: {e}")
#         return {"status": "failed", "error": str(e)}

# @app.route("/influencer_data_pipeline", methods=["GET"])
# def influencer_data_pipeline():
#     try:
#         source_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "taippa_influencer_v3_source")
#         target_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "influencers_instagram_v3")

#         source_records = source_table.all()

#         for record in source_records:
#             fields = record.get("fields", {})
#             raw_handle = fields.get("instagram_handle", "")

#             if not raw_handle:
#                 continue

#             # Normalize handle (strip @, lowercase, remove spaces)
#             instagram_handle = raw_handle.lstrip("@").strip().lower()
#             if not instagram_handle:
#                 continue

#             # Check if already exists in target (case-insensitive)
#             formula = f"LOWER({{instagram_username}}) = \"{instagram_handle}\""
#             existing = target_table.all(formula=formula)

#             if existing:
#                 print(f"⏩ Skipping {instagram_handle}, already exists.")
#                 continue

#             print(f"🚀 Starting pipeline for {instagram_handle}...")

#             # Run profile scraper
#             profile_data = profile_scraper(
#                 instagram_handle,
#                 fields.get("niche"),
#                 fields.get("primary_location_country")
#             )
#             if not profile_data or not isinstance(profile_data, dict):
#                 print(f"⚠️ Profile scraper failed for {instagram_handle}, skipping...")
#                 continue

#             # Run post scraper
#             followers_count = profile_data.get("instagram_followers_count") or 1
#             post_data = post_scraper(instagram_handle, posts_count=5, followers_count=followers_count)
#             if not post_data or not isinstance(post_data, dict):
#                 print(f"⚠️ Post scraper failed for {instagram_handle}, skipping...")
#                 continue

#             # Engagement rate fetch
#             try:
#                 engagement_info = asyncio.get_event_loop().run_until_complete(
#                     get_engagement_rate([instagram_handle])
#                 )
#                 engagement_rate = (
#                     engagement_info[0].get("engagement_rate_pct", 0)
#                     if engagement_info and isinstance(engagement_info, list)
#                     else 0
#                 )
#             except Exception as e:
#                 print(f"⚠️ Engagement rate fetch failed for {instagram_handle}: {e}")
#                 engagement_rate = 0

#             post_data["engagement_rate"] = engagement_rate  # overwrite or update

#             # Build normalized record with all values as strings
#             combined_data = {}

#             # Profile data mapping
#             profile_mapping = {
#                 "instagram_url": str(profile_data.get("instagram_url", "")),
#                 "instagram_username": instagram_handle,  # always normalized
#                 "full_name": str(profile_data.get("full_name", "")),
#                 "instagram_bio": str(profile_data.get("instagram_bio", "")),
#                 "external_urls": str(profile_data.get("external_urls", "")),
#                 "instagram_followers_count": str(profile_data.get("instagram_followers_count", "")),
#                 "instagram_follows_count": str(profile_data.get("instagram_follows_count", "")),
#                 "business_category_name": str(profile_data.get("business_category_name", "")),
#                 "instagram_profile_pic": str(profile_data.get("instagram_profile_pic", "")),
#                 "instagram_posts_count": str(profile_data.get("instagram_posts_count", "")),
#                 # "influencer_type": str(profile_data.get("influencer_type", "")),
#                 # "influencer_location": str(profile_data.get("influencer_location", "")),
#             }
#             combined_data.update(profile_mapping)

#             # Post data mapping
#             post_mapping = {
#                 "instagram_captions": str(post_data.get("instagram_captions", "")),
#                 "instagram_hashtags": str(post_data.get("instagram_hashtags", "")),
#                 "instagram_post_urls": str(post_data.get("instagram_post_urls", "")),
#                 "instagram_comments_counts": str(post_data.get("instagram_comments_counts", "")),
#                 "instagram_video_play_counts": str(post_data.get("instagram_video_play_counts", "")),
#                 "instagram_video_urls": str(post_data.get("instagram_video_urls", "")),
#                 "instagram_likes_counts": str(post_data.get("instagram_likes_counts", "")),
#                 "avg_comments": str(post_data.get("avg_comments", "")),
#                 "avg_likes": str(post_data.get("avg_likes", "")),
#                 "avg_video_play_counts": str(post_data.get("avg_video_play_counts", "")),
#                 "engagement_rate": str(post_data.get("engagement_rate", "")),  # updated
#                 "videos_engagement": str(post_data.get("estimated_reach", "")),
#             }
#             combined_data.update(post_mapping)

#             # Source fields mapping
#             source_mapping = {
#                 "full_name": str(fields.get("full_name", "")),
#                 "top_categories": str(fields.get("top_categories", "")),
#                 "influencer_tier": str(fields.get("influencer_tier", "")),
#                 "gender": str(fields.get("gender", "")),
#                 "top_interests": str(fields.get("top_interest", "")),
#                 "phone": str(fields.get("phone", "")),
#                 "email_id": str(fields.get("email_id", "")),
#                 "cities_in_bio": str(fields.get("primary_loaction_city", "")),
#                 "countries_in_bio": str(fields.get("primary_location_country", "")),
#                 "preferred_contact_method": str(fields.get("preferred_contact_method", "")),
#                 "confidence": str(fields.get("confidence", "")),
#                 "reasoning": str(fields.get("reasoning", "")),
#             }
#             combined_data.update(source_mapping)

#             # Insert into Airtable
#             try:
#                 response = target_table.create(combined_data)
#                 print(f"✅ Inserted {instagram_handle} → {response['id']}")
#             except Exception as e:
#                 print(f"❌ Failed to insert {instagram_handle}: {e}")

#         return {"status": "passed", "message": "Pipeline executed successfully"}

#     except Exception as e:
#         print(f"❌ Error in influencer_data_pipeline: {e}")
#         return {"status": "failed", "error": str(e)}

@app.route("/influencer_data_pipeline", methods=["GET"])
def influencer_data_pipeline():
    try:
        source_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "taippa_influencer_v3_source")
        target_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "influencers_instagram_v3")

        source_records = source_table.all()

        for record in source_records:
            fields = record.get("fields", {})
            raw_handle = fields.get("instagram_handle", "")

            if not raw_handle:
                continue

            # Normalize handle (strip @, lowercase, remove spaces)
            instagram_handle = raw_handle.lstrip("@").strip().lower()
            if not instagram_handle:
                continue

            # Check if already exists in target (case-insensitive)
            formula = f"LOWER({{instagram_username}}) = \"{instagram_handle}\""
            existing = target_table.all(formula=formula)

            if existing:
                print(f"⏩ Skipping {instagram_handle}, already exists.")
                continue

            print(f"🚀 Starting pipeline for {instagram_handle}...")

            # Run profile scraper
            profile_data = profile_scraper(
                instagram_handle,
                fields.get("niche"),
                fields.get("primary_location_country")
            )
            if not profile_data or not isinstance(profile_data, dict):
                print(f"⚠️ Profile scraper failed for {instagram_handle}, skipping...")
                continue

            # Run post scraper
            followers_count = profile_data.get("instagram_followers_count") or 1
            post_data = post_scraper(instagram_handle, posts_count=5, followers_count=followers_count)
            if not post_data or not isinstance(post_data, dict):
                print(f"⚠️ Post scraper failed for {instagram_handle}, skipping...")
                continue

            # Engagement rate fetch
            try:
                engagement_info = asyncio.get_event_loop().run_until_complete(
                    get_engagement_rate([instagram_handle])
                )

                if engagement_info:
                    engagement_item = engagement_info[0]
                    engagement_rate = engagement_item.get("engagement_rate", 0)
                    avg_likes = engagement_item.get("average_likes", "")
                    avg_comments = engagement_item.get("average_comments", "")
                    avg_views = engagement_item.get("average_views", "")
                else:
                    engagement_rate = 0
                    avg_likes = avg_comments = avg_views = ""

            except Exception as e:
                print(f"❌ Engagement fetch failed for {normalized_handle}: {e}")
                engagement_rate = 0
                avg_likes = avg_comments = avg_views = ""

            # Build normalized record with all values as strings
            combined_data = {}

            # Profile data mapping
            profile_mapping = {
                "instagram_url": str(profile_data.get("instagram_url", "")),
                "instagram_username": instagram_handle,  # always normalized
                "full_name": str(profile_data.get("full_name", "")),
                "instagram_bio": str(profile_data.get("instagram_bio", "")),
                "external_urls": str(profile_data.get("external_urls", "")),
                "instagram_followers_count": str(profile_data.get("instagram_followers_count", "")),
                "instagram_follows_count": str(profile_data.get("instagram_follows_count", "")),
                "business_category_name": str(profile_data.get("business_category_name", "")),
                "instagram_profile_pic": str(profile_data.get("instagram_profile_pic", "")),
                "instagram_posts_count": str(profile_data.get("instagram_posts_count", "")),
                # "influencer_type": str(profile_data.get("influencer_type", "")),
                # "influencer_location": str(profile_data.get("influencer_location", "")),
            }
            combined_data.update(profile_mapping)

            # Post data mapping
            post_mapping = {
                "instagram_captions": str(post_data.get("instagram_captions", "")),
                "instagram_hashtags": str(post_data.get("instagram_hashtags", "")),
                "instagram_post_urls": str(post_data.get("instagram_post_urls", "")),
                "instagram_comments_counts": str(post_data.get("instagram_comments_counts", "")),
                "instagram_video_play_counts": str(post_data.get("instagram_video_play_counts", "")),
                "instagram_video_urls": str(post_data.get("instagram_video_urls", "")),
                "instagram_likes_counts": str(post_data.get("instagram_likes_counts", "")),
                # "avg_comments": str(post_data.get("avg_comments", "")),
                # "avg_likes": str(post_data.get("avg_likes", "")),
                # "avg_video_play_counts": str(post_data.get("avg_video_play_counts", "")),
                # "engagement_rate": str(post_data.get("engagement_rate", "")),  # updated
                # "videos_engagement": str(post_data.get("estimated_reach", "")),
                "avg_likes": str(avg_likes),
                "avg_comments": str(avg_comments),
                "avg_video_play_counts": str(avg_views),
                "engagement_rate": str(engagement_rate),
                "videos_engagement": str(avg_views),
            }
            combined_data.update(post_mapping)

            # Source fields mapping
            source_mapping = {
                "full_name": str(fields.get("full_name", "")),
                "top_categories": str(fields.get("top_categories", "")),
                "influencer_tier": str(fields.get("influencer_tier", "")),
                "gender": str(fields.get("gender", "")),
                "top_interests": str(fields.get("top_interest", "")),
                "phone": str(fields.get("phone", "")),
                "email_id": str(fields.get("email_id", "")),
                "cities_in_bio": str(fields.get("primary_loaction_city", "")),
                "countries_in_bio": str(fields.get("primary_location_country", "")),
                "preferred_contact_method": str(fields.get("preferred_contact_method", "")),
                "confidence": str(fields.get("confidence", "")),
                "reasoning": str(fields.get("reasoning", "")),
            }
            combined_data.update(source_mapping)

            # Insert into Airtable
            try:
                response = target_table.create(combined_data)
                print(f"✅ Inserted {instagram_handle} → {response['id']}")
            except Exception as e:
                print(f"❌ Failed to insert {instagram_handle}: {e}")

        return {"status": "passed", "message": "Pipeline executed successfully"}

    except Exception as e:
        print(f"❌ Error in influencer_data_pipeline: {e}")
        return {"status": "failed", "error": str(e)}

 
@app.route('/extract_external_url', methods=['POST'])
def extract_endpoint():
    data = request.get_json()
    if not data or 'external_url' not in data:
        return jsonify({"error": "Missing 'external_url' parameter"}), 400

    external_url = data['external_url']
    instagram_followers_count = data.get("instagram_followers_count", 0)

    if not isinstance(external_url, str):
        return jsonify({"error": "'external_url' must be a string"}), 400

    result = extract_info(external_url, instagram_followers_count)
    return jsonify(result), 200


@app.route('/registered_influencer_sanitization_module', methods=['GET', 'POST'])
def influencer_sanitization_module():
    data_list = []

    if request.method == "POST" and request.is_json:
        json_data = request.get_json()
        if isinstance(json_data, list):
            data_list = json_data
        elif isinstance(json_data, dict):
            data_list = [json_data]
        else:
            return jsonify({"error": "Invalid JSON format"}), 400

    elif request.method == "GET":
        influencer_data = {
            "first_name": request.args.get("first_name"),
            "phone_number": request.args.get("phone_number"),
            "instagram_handle": request.args.get("instagram_handle"),
            "tiktok_handle": request.args.get("tiktok_handle"),
            "facebook_handle": request.args.get("facebook_handle"),
            "twitter_handle": request.args.get("twitter_handle"),
            "snapchat_handle": request.args.get("snapchat_handle"),
            "location": request.args.get("location")                   
        }
        data_list = [influencer_data]

    else:
        return jsonify({"error": "Unsupported request format. Use GET with query params or POST JSON."}), 400

    results = [clean_data(data) for data in data_list]
    return jsonify(results), 200

@app.route("/update_campaign_metrics", methods=["GET"])
def update_campaign_metrics_endpoint():
    try:
        campaign_id = request.args.get("campaign_id")
        posts_count = request.args.get("posts_count", type=int)
        instagram_username = request.args.get("instagram_username")
        
        # Get and parse hashtags_required as list
        raw_hashtags = request.args.get("hashtags_required")
        hashtags_required = json.loads(raw_hashtags) if raw_hashtags else []

        if not campaign_id or not instagram_username or not hashtags_required:
            return jsonify({"status": "failed", "message": "Missing input parameters"}), 400

        status = update_campaign_metrics_v3(
            campaign_id,
            instagram_username,
            posts_count,
            hashtags_required
        )

        if status:
            return jsonify({"status": "passed", "content": "Campaign metrics updated successfully"}), 200
        else:
            return jsonify({"status": "failed", "content": "Failed to update campaign metrics"}), 500

    except Exception as e:
        print(f"Error occurred while updating Campaign metrics: {e}")
        return jsonify({"status": "failed", "content": f"Failed to update campaign metrics {e}"}), 500


@app.route('/upload-profile-pic-from-url', methods=['GET', 'POST'])
def upload_pic_from_url():
    if request.method == 'POST':
        data = request.get_json()
        profile_pic_url = data.get("profile_pic_url")
        record_id = data.get("record_id")

    elif request.method == 'GET':
        profile_pic_url = request.args.get("profile_pic_url")
        record_id = request.args.get("record_id")

    else:
        return jsonify({"status": "failed", "message": "Unsupported method"}), 405

    if not profile_pic_url or not record_id:
        return jsonify({"status": "failed", "message": "Missing profile_pic_url or record_id"}), 400

    result, status = process_and_upload_image(profile_pic_url, record_id)
    return jsonify(result), status


@app.route('/image-recognition-instagram-dict', methods=['GET', 'POST'])
def image_recognition_endpoint_dict():
    data = []

    if request.method == 'POST' and request.is_json:
        json_data = request.get_json()
        if isinstance(json_data, dict) and 'post_urls' in json_data:
            urls = json_data['post_urls']
            if isinstance(urls, list):
                data = urls
            elif isinstance(urls, str):
                data = [urls.strip()]
            else:
                return jsonify({"error": "'post_urls' must be a list or string"}), 400
        else:
            return jsonify({"error": "Missing or invalid 'post_urls' in JSON"}), 400

    elif request.method == 'GET':
        raw_input = request.args.get("post_urls", "").strip()
        if not raw_input:
            return jsonify({"error": "Missing 'post_urls' query parameter"}), 400

        try:
            
            parsed_list = ast.literal_eval(raw_input)
            if not isinstance(parsed_list, list):
                raise ValueError
            data = [url.strip() for url in parsed_list if isinstance(url, str)]
            if data == []:
                return jsonify({
                    "results": "",
                    "all_post_urls": "",
                    "all_image_urls": "",
                    "all_drive_urls": "",
                    "all_tags": ""
                }), 200
        except Exception:
            return jsonify({"error": "Invalid format for 'post_urls'. Must be a list-like string."}), 400

    else:
        return jsonify({"error": "Unsupported request format. Use GET with query params or POST with JSON."}), 400

    if not data:
        return jsonify({"error": "No valid Instagram post URLs provided"}), 400

    return image_analysis_endpoint({"post_urls": data})

@app.route('/image-recognition-instagram', methods=['GET'])
def image_recognition_endpoint():
    result = extract_images()
    if result.get("status") == "error":
        return jsonify(result), 500
    return jsonify(result), 200

    
@app.route('/image-uploading_into_google_slide', methods=['GET', 'POST'])
def image_upload_endpoint():
    try:
        if request.method == 'POST':
            data = request.get_json()
            record_id = data.get('record_id') if data else None
        else:  # GET
            record_id = request.args.get('record_id')

        if not record_id:
            return jsonify({"status": "failed", "message": "Missing record_id"}), 400

        result = insert_image_from_airtable(record_id)

        if result.get("status") == "error":
            return jsonify(result), 404

        return jsonify(result), 200

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"status": "failed", "message": str(e)}), 500


######### ROUTES - INFLUENCER MARKETING ##########

@app.route("/store_meeting_data", methods=["GET"])
def store_meeting_data():
    try:
        meeting_data = request.args.get("meeting_data")
        client_id = request.args.get("client_id")
        if not meeting_data or not client_id:
            return jsonify({"status": "failed", "content": "Missing 'meeting_data' or 'client_id' parameter"}), 400
        
        # Assuming meeting_data is a JSON string, you can parse it if needed
        # For now, we will just return it as is
        return jsonify({"status": "passed", "content": str(populate_meeting_notes(meeting_data,client_id))})
    except Exception as e:
        print(f"Error occurred while storing meeting data: {e}")
        return jsonify({"status": "failed", "content": "Error occurred while storing meeting data"}), 500

@app.route('/get_notion_page_text', methods=['GET'])
def get_notion_page_content():
    try:
        auth_token = request.args.get('auth_token')
        page_id = request.args.get('page_id')
        if not auth_token or not page_id:
            return jsonify({"status": "failed", "content": "Missing 'auth_token' or 'page_id' parameter"}), 400
        return ({"status": "passed", "content": get_notion_page_text(auth_token, page_id)})
    except Exception as e:
        print(f"Error occurred while fetching Notion page text: {e}")
        return jsonify({"status": "failed", "content": "Error occurred while fetching Notion page text"}), 500

@app.route('/generate_airtable_formula', methods=['GET'])
def generate_airtable_formula():
    try:
        user_query = request.args.get("user_query")
        influencer_table = request.args.get("influencer_table")
        if not user_query or not influencer_table:
            return jsonify({"status": "failed", "content": "Missing 'table_name' or 'formula' parameter"})
        formula = airtable_formula_generator(influencer_table,user_query)
        return jsonify({"status": "passed", "content": formula})
    except Exception as e:
        print(f"Error occurred while generating Airtable formula: {e}")
        return jsonify({"status": "failed", "content": "Error occurred while generating Airtable formula"})
    
@app.route('/fetch_airtable_data_via_formula', methods=['GET'])
def fetch_airtable_data_via_formula():
    try:
        formula = request.args.get("formula")
        if not formula:
            return jsonify({"status": "failed", "content": "Missing 'formula' parameter"})
        filtered_airtable_data = fetch_records_from_airtable_with_formula(formula)
        return jsonify({"status": "passed", "content": filtered_airtable_data})
    except Exception as e:
        print(f"Error occurred while fetching Airtable data from formula: {e}")
        return jsonify({"status": "failed", "content": "Error occurred while fetching Airtable data from formula"})



@app.route('/upload', methods=['GET'])
def upload_page():
    return render_template("upload_form.html")

@app.route('/submit_influencer_form_data', methods=['POST'])
def submit_influencer_form():
    try:
        brand_id = request.form.get("brand_id")
        files = request.files.getlist("documents")

        if not brand_id or not files:
            return jsonify({"status": "failed", "content": "Missing brand_id or documents"}), 400

        return handle_upload_and_submit_to_airtable(brand_id, files)
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"status": "failed", "message": str(e)}), 500
@app.route("/submit_influencer_form_data", methods=["POST"])
def submit_form():
    brand_id = request.form.get("brand_id")
    files = request.files.getlist("documents")
    images = request.files.getlist("images")

    if not brand_id or (not files and not images):
        return jsonify({"error": "Missing brand_id or files/images"}), 400

    return handle_upload_and_submit_to_airtable(brand_id, files, images)

@app.route('/get_data_entrichment_using_gpt_module', methods=['GET', 'POST'])
def data_entrichment_using_gpt_module():
    data_list = []

    if request.method == "POST" and request.is_json:
        json_data = request.get_json()
        if isinstance(json_data, list):
            data_list = json_data
        elif isinstance(json_data, dict):
            data_list = [json_data]
        else:
            return jsonify({"error": "Invalid JSON format"}), 400

    elif request.method == "GET":
        influencer_data = {
            "created_time": request.args.get("created_time"),
            "email_id": request.args.get("email_id"),
            "external_urls": request.args.get("external_urls"),
            "full_name": request.args.get("full_name"),
            "id": request.args.get("id"),
            "influencer_location": request.args.get("influencer_location"),
            "influencer_nationality": request.args.get("influencer_nationality"),
            "influencer_type": request.args.get("influencer_type"),
            "instagram_url": request.args.get("instagram_url"),
            "phone": request.args.get("phone"),
            "profile_type": request.args.get("profile_type"),
            "social_media_profile_type": request.args.get("social_media_profile_type", "tiktok"),
            "targeted_audience": request.args.get("targeted_audience"),
            "tiktok_audience_location": request.args.get("tiktok_audience_location"),
            "tiktok_bio": request.args.get("tiktok_bio"),
            "tiktok_comment_count": request.args.get("tiktok_comment_count"),
            "tiktok_content_style": request.args.get("tiktok_content_style"),
            "tiktok_content_type": request.args.get("tiktok_content_type"),
            "tiktok_digg_count": request.args.get("tiktok_digg_count"),
            "tiktok_followers_count": request.args.get("tiktok_followers_count"),
            "tiktok_follows_count": request.args.get("tiktok_follows_count"),
            "tiktok_influencer_summary": request.args.get("tiktok_influencer_summary"),
            "tiktok_language_used": request.args.get("tiktok_language_used"),
            "tiktok_likes_count": request.args.get("tiktok_likes_count"),
            "tiktok_niche": request.args.get("tiktok_niche"),
            "tiktok_play_count": request.args.get("tiktok_play_count"),
            "tiktok_profile_pic": request.args.get("tiktok_profile_pic"),
            "tiktok_share_count": request.args.get("tiktok_share_count"),
            "tiktok_suitable_brands": request.args.get("tiktok_suitable_brands"),
            "tiktok_targeted_audience": request.args.get("tiktok_targeted_audience"),
            "tiktok_text": request.args.get("tiktok_text"),
            "tiktok_url": request.args.get("tiktok_url"),
            "tiktok_username": request.args.get("tiktok_username"),
            "tiktok_video_urls": request.args.get("tiktok_video_urls"),
            "tiktok_videos_count": request.args.get("tiktok_videos_count")
            
        }
        data_list = [influencer_data]

    else:
        return jsonify({"error": "Unsupported request format. Use GET with query params or POST JSON."}), 400

    results = [data_entrichment_using_gpt_airtable(data) for data in data_list]
    return jsonify(results), 200

@app.route("/upload-sanitized-tiktok-data", methods=["POST", "GET"])
def upload_sanitized_tiktok_data():
    data_list = []

    if request.method == "POST" and request.is_json:
        json_data = request.get_json()
        if isinstance(json_data, list):
            data_list = json_data
        elif isinstance(json_data, dict):
            data_list = [json_data]
        else:
            return jsonify({"error": "Invalid JSON format"}), 400

    elif request.method == "GET":
        influencer_data = {
            "created_time": request.args.get("created_time"),
            "email_id": request.args.get("email_id"),
            "external_urls": request.args.get("external_urls"),
            "full_name": request.args.get("full_name"),
            "id": request.args.get("id"),
            "influencer_location": request.args.get("influencer_location"),
            "influencer_nationality": request.args.get("influencer_nationality"),
            "influencer_type": request.args.get("influencer_type"),
            "instagram_url": request.args.get("instagram_url"),
            "phone": request.args.get("phone"),
            "profile_type": request.args.get("profile_type"),
            "social_media_profile_type": request.args.get("social_media_profile_type", "tiktok"),
            "targeted_audience": request.args.get("targeted_audience"),
            "tiktok_audience_location": request.args.get("tiktok_audience_location"),
            "tiktok_bio": request.args.get("tiktok_bio"),
            "tiktok_comment_count": request.args.get("tiktok_comment_count"),
            "tiktok_content_style": request.args.get("tiktok_content_style"),
            "tiktok_content_type": request.args.get("tiktok_content_type"),
            "tiktok_digg_count": request.args.get("tiktok_digg_count"),
            "tiktok_followers_count": request.args.get("tiktok_followers_count"),
            "tiktok_follows_count": request.args.get("tiktok_follows_count"),
            "tiktok_influencer_summary": request.args.get("tiktok_influencer_summary"),
            "tiktok_language_used": request.args.get("tiktok_language_used"),
            "tiktok_likes_count": request.args.get("tiktok_likes_count"),
            "tiktok_niche": request.args.get("tiktok_niche"),
            "tiktok_play_count": request.args.get("tiktok_play_count"),
            "tiktok_profile_pic": request.args.get("tiktok_profile_pic"),
            "tiktok_share_count": request.args.get("tiktok_share_count"),
            "tiktok_suitable_brands": request.args.get("tiktok_suitable_brands"),
            "tiktok_targeted_audience": request.args.get("tiktok_targeted_audience"),
            "tiktok_text": request.args.get("tiktok_text"),
            "tiktok_url": request.args.get("tiktok_url"),
            "tiktok_username": request.args.get("tiktok_username"),
            "tiktok_video_urls": request.args.get("tiktok_video_urls"),
            "tiktok_videos_count": request.args.get("tiktok_videos_count")
        }
        data_list = [influencer_data]

    else:
        return jsonify({"error": "Unsupported request format. Use GET with query params or POST JSON."}), 400

    result = sanitize_and_upload_tiktok_data(data_list)
    return jsonify(result), 200

@app.route("/upload-sanitized", methods=["POST", "GET"])
def upload_sanitized():
    data_list = []

    if request.method == "POST" and request.is_json:
        json_data = request.get_json()
        if isinstance(json_data, list):
            data_list = json_data
        elif isinstance(json_data, dict):
            data_list = [json_data]
        else:
            return jsonify({"error": "Invalid JSON format"}), 400

    elif request.method == "GET":
        influencer_data = {
            "instagram_url": request.args.get("instagram_url"),
            "instagram_username": request.args.get("instagram_username"),
            "full_name": request.args.get("full_name"),
            "instagram_bio": request.args.get("instagram_bio"),
            "external_urls": request.args.get("external_urls"),
            "instagram_followers_count": request.args.get("instagram_followers_count"),
            "instagram_follows_count": request.args.get("instagram_follows_count"),
            "business_category_name": request.args.get("business_category_name"),
            "instagram_profile_pic": request.args.get("instagram_profile_pic"),
            "instagram_posts_count": request.args.get("instagram_posts_count"),
            "instagram_captions": request.args.get("trimmed_instagram_caption"),
            "instagram_hashtags": request.args.get("trimmed_instagram_caption"),
            "instagram_post_urls": request.args.get("instagram_post_urls"),
            "instagram_comments_counts": request.args.get("instagram_comments_counts"),
            "instagram_likes_counts": request.args.get("instagram_likes_counts"),
            "instagram_video_play_counts": request.args.get("instagram_video_play_counts"),
            "instagram_video_urls": request.args.get("video_urls"),
            "avg_comments": request.args.get("avg_comments"),
            "avg_likes": request.args.get("avg_likes"),
            "avg_video_play_counts": request.args.get("avg_video_play_counts"),
            "influencer_type": request.args.get("influencer_type"),
            "influencer_location": request.args.get("influencer_location"),
            "influencer_nationality": request.args.get("influencer_nationality"),
            "targeted_audience": request.args.get("targeted_audience"),
            "targeted_domain": request.args.get("targeted_domain"),
            "profile_type": request.args.get("profile_type"),
            "email_id": request.args.get("email"),
            # "tiktok_url": request.args.get("tiktok_id"),
            "tiktok_url": request.args.get("tiktok_url"),
            "twitter_url": request.args.get("twitter_id"),
            "snapchat_url": request.args.get("snapchat_id"),
            "linkedin_url": request.args.get("linkedin_id"),
            "phone": request.args.get("phone"),
            "social_media_profile_type": request.args.get("social_media_profile_type", "instagram"),  # fallback
            "engagement_rate": request.args.get("engagement_rate"),
            "estimated_reach": request.args.get("estimated_reach")
        }
        data_list = [influencer_data]
    else:
        return jsonify({"error": "Unsupported request format. Use GET with query params or POST JSON."}), 400

    result = sanitize_data_instagram(data_list)
    return jsonify(result), 200

@app.route("/register_influencer_form_tracker", methods=["POST"])
def run_influencer_form_tracker():
    try:
        return influencer_form_tracker()
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/data_entrichment_using_gpt_psql', methods=['GET'])
def data_entrichment_using_gpt_psql():
    try:
        tiktok_username = request.args.get("username")
        if not tiktok_username:
            return jsonify({"status": "failed", "content": "Missing 'username' parameter"})
        
        result = data_entrichment_using_gpt(tiktok_username)

        if result["status"] == "failed":
            return jsonify({"status": "failed", "content": result.get("message", "Unknown error")})

        return jsonify({"status": "passed", "content": result})

    except Exception as e:
        print(f"Error occurred : {e}")
        return jsonify({"status": "failed", "content": "Error occurred "})
    
@app.route('/scrape_influencers_google_search_psql', methods=['GET', 'POST'])
def scrape_through_google_psql():
    if request.method == 'POST':
        data = request.get_json(force=True)
        media = request.args.get('media', '').strip()
        influencer_type = request.args.get('influencer_type', '').strip()
        influencer_location = request.args.get('influencer_location', '').strip()
        page = request.args.get("page", 1, type=int)
    else:  # GET
        data = None
        media = request.args.get('media', '').strip()
        influencer_type = request.args.get('influencer_type', '').strip()
        influencer_location = request.args.get('influencer_location', '').strip()
        page = request.args.get("page", 1, type=int)

    if not (media and influencer_type and influencer_location):
        return jsonify({
            "status": "failed",
            "error": "Missing one or more required parameters: media, influencer_type, influencer_location"
        }), 400

    return scrape_influencers_psql(data, media, influencer_type, influencer_location, page)

@app.route('/scrape_influencers_google_search', methods=['GET', 'POST'])
def scrape_through_google():
    if request.method == 'POST':
        data = request.get_json(force=True)
        media = request.args.get('media', '').strip()
        influencer_type = request.args.get('influencer_type', '').strip()
        influencer_location = request.args.get('influencer_location', '').strip()
        page = request.args.get("page", 1, type=int)
    else:  # GET
        data = None
        media = request.args.get('media', '').strip()
        influencer_type = request.args.get('influencer_type', '').strip()
        influencer_location = request.args.get('influencer_location', '').strip()
        page = request.args.get("page", 1, type=int)

    if not (media and influencer_type and influencer_location):
        return jsonify({
            "status": "failed",
            "error": "Missing one or more required parameters: media, influencer_type, influencer_location"
        }), 400

    return scrape_influencers(data, media, influencer_type, influencer_location, page)


@app.route('/calculate_metrics', methods=['GET', 'POST'])
def calculate_metrics_instagram():
    try:
        if request.method == 'GET':
            username = request.args.get("username")
            reach_rate = float(request.args.get("reach_rate", 0.35))
        else:
            data = request.get_json(force=True)
            username = data.get("username")
            reach_rate = float(data.get("reach_rate", 0.35))

        if not username:
            return jsonify({"status": "failed", "error": "Missing 'username' parameter"}), 400

        result, status = calculate_metrics(username, reach_rate)
        return jsonify(result), status

    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500

@app.route('/tiktok_posts_to_airtable_psql', methods=['GET', 'POST'])
def scrape_route_psql():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username') if data else None
    else:  # GET
        username = request.args.get('username')
    if not username:
        return jsonify({"status": "failed", "error": "Username is required"}), 400
    result = scrape_and_store_psql(username)
    return jsonify(result)


@app.route('/tiktok_posts_to_airtable', methods=['GET', 'POST'])
def scrape_route():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username') if data else None
    else:  # GET
        username = request.args.get('username')
    if not username:
        return jsonify({"status": "failed", "error": "Username is required"}), 400
    result = scrape_and_store(username)
    return jsonify(result)

@app.route('/scrape_tiktok_profile_psql', methods=['GET'])
def scrape_tiktok_profile_endpoint_psql():
    try:
        tiktok_username = request.args.get("username")
        
        if not tiktok_username:
            return jsonify({"status": "failed", "content": "Missing 'tiktok_username' parameter"})
        result = scrape_tiktok_profile_psql(tiktok_username)
        if result["status"] == "failed":
            return jsonify({"status": "failed", "content": result.get("error", "Unknown error")})
        return jsonify({"status": "passed", "content": result})
    except Exception as e:
        print(f"Error occurred : {e}")
        return jsonify({"status": "failed", "content": "Error occurred "})
    
@app.route('/scrape_tiktok_profile', methods=['GET'])
def scrape_tiktok_profile_endpoint():
    try:
        tiktok_username = request.args.get("username")
        
        if not tiktok_username:
            return jsonify({"status": "failed", "content": "Missing 'tiktok_username' parameter"})
        result = scrape_tiktok_profile(tiktok_username)
        if result["status"] == "failed":
            return jsonify({"status": "failed", "content": result.get("error", "Unknown error")})
        return jsonify({"status": "passed", "content": result})
    except Exception as e:
        print(f"Error occurred : {e}")
        return jsonify({"status": "failed", "content": "Error occurred "})


########## INFLUENCER MARKETING ROUTES ##########

@app.route("/duplicate_check_influencer")
def duplicate_check_influencer_data():
    try:
        primary_key_column = request.args.get("primary_key_column")
        primary_key_value = request.args.get("primary_key_value")
        table_name = request.args.get("table_name")
        status = db_manager.unique_key_check(primary_key_column,primary_key_value,table_name)
        return {"status":"success","content":status}
    except Exception as e:
        return {"status":"failed","content":f"Error occurred during unique key check: {e}"}

@app.route("/influencer_table_trigger")
def retrieve_latest_records():
    try:
        campaign_id = request.args.get("campaign_id")
        social_media_type = request.args.get("social_media_type")
        return {"status":"success","content":influencer_table_trigger(campaign_id,social_media_type)}
    except Exception as e:
        print(f"Error occured while executing influencer trigger. {e}")
        return {"status":"failed","content":f"Error occurred while processing influencer brief: {e}"}

@app.route("/process_influencer_brief", methods=["GET"])
def process_influencer_brief():
    try:
        # Airtable
        drive_urls = request.args.get("drive_urls")
        client_id = request.args.get("client_id")
        # drive_urls = """["https://drive.google.com/uc?id=1IoCxHQP8dKBgrGLjeUcDq75Y9Ip97dVf&export=download"]"""
        # drive_urls = '["https://drive.google.com/uc?id=1LsB71VCGuoQG_r67l2oWzpFKh5zrvosf&export=download"]'
        # client_id = "sls"
        airtable_fields = """
        Database schema with column descriptions:
            Table: src_influencer_data (
            id                          long text -- Unique identifier for the influencer
            instagram_url               long text -- URL of the influencer's Instagram profile (if null it would have values as '', 'NA','N/A')
            instagram_followers_count   Long text -- Number of followers on Instagram
            instagram_username          Long text -- Instagram username/handle
            instagram_bio               Long text -- Bio text from the Instagram profile
            influencer_type             Long text -- Type/category of influencer (fixed category values among this: [food_vlogger,fashion_vlogger,real_estate_influencers,business_vloggers,finance_vloggers,real_estate_influencers,beauty_vlogger,tech_vloggers])
            influencer_location         Long text -- Location of the influencer
            instagram_post_urls         Long text -- List of URLs to the influencer's Instagram posts
            business_category_name      Long text -- Main business category of the influencer (Tag provided by Instagram for Business profile Eg: "Personal blog","Digital creator","Reel creator" etc)
            full_name                   Long text -- Full name of the influencer
            instagram_follows_count     Long text -- Number of accounts the influencer follows
            created_time                Long text -- Timestamp when the influencer was added to the database
            instagram_hashtags          Long text -- Hashtags used by the influencer for different posts (stored as list of strings)
            instagram_captions          Long text -- Captions from the influencer's posts (stored as list of strings)
            instagram_video_play_counts Long text -- Number of plays for video posts (stored as list of strings)
            instagram_likes_counts      Long text -- Number of likes on posts (stored as list of strings)
            instagram_comments_counts   Long text -- Number of comments on posts (stored as list of strings)
            instagram_video_urls        Long text -- URLs of video posts
            instagram_posts_count       Long text -- Total number of posts by the influencer
            external_urls               Long text -- List of external links provided by the influencer
            instagram_profile_pic       Long text -- URL of the influencer's profile picture
            influencer_nationality      Long text -- Nationality of the influencer (Include country names, can be case sensitive)
            targeted_audience           Long text -- Target audience group for the influencer (fixed category values among this: ["gen-z","gen-y", "gen-x"])
            targeted_domain             Long text -- Domain or industry targeted by the influencer (Can only have fixed category values among this: ["food", "fashion", "fitness", "gaming", "education", "automotive", "finance", "art"])
            profile_type                Long text -- Type of profile (fixed category values among this: ["person","group"])
            email_id                    Long text -- Email address of the influencer (if not available value is "NA" or "")
            twitter_url                 Long text -- URL of the influencer's Twitter profile
            snapchat_url                Long text -- URL of the influencer's Snapchat profile
            phone                       Long text -- Phone number of the influencer ( if not available value is "NA" or "")
            linkedin_url                Long text -- URL of the influencer's LinkedIn profile
            tiktok_url                  Long text -- URL of the influencer's TikTok profile
            )
        """
        airtable_fields = """
        Airtable Schema for Table: `src_influencer_data`

        """
        print(drive_urls)
        if drive_urls in ["", None] or client_id in ["", None]:
            return {"status":"failed","content":"Missing input parameters while processing influencer brief"}
        brand_query,formula = influencer_brief_processing(drive_urls, client_id,airtable_fields)
        return {"status":"success","content":{"brand_query": brand_query, "formula": formula}}
    except Exception as e:
        print(f"Error occurred while processing influencer brief: {e}")
        return {"status":"failed","content":f"Error occurred while processing influencer brief: {e}"}


# http://127.0.0.1:5000/analyze_social_profile?instagram_bio=Hello%20World&influencer_location=Dubai&trimmed_instagram_caption=This%20is%20a%20test%20caption&instagram_url=https://www.instagram.com/testuser/&business_category_name=Influencer&trimmed_instagram_hashtags=fashion,food
@app.route("/add_influencer_data_instagram", methods=["GET"])
def add_influencer_data_in_db():
    try:
        influencer_data = {
            "instagram_url": request.args.get("instagram_url"),
            "instagram_username": request.args.get("instagram_username"),
            "full_name": request.args.get("full_name"),
            "instagram_bio": request.args.get("instagram_bio"),
            "external_urls": request.args.get("external_urls"),
            "instagram_followers_count": request.args.get("instagram_followers_count"),
            "instagram_follows_count": request.args.get("instagram_follows_count"),
            "business_category_name": request.args.get("business_category_name"),
            "instagram_profile_pic": request.args.get("instagram_profile_pic"),
            "instagram_posts_count": request.args.get("instagram_posts_count"),
            "instagram_captions": request.args.get("trimmed_instagram_caption"),
            "instagram_hashtags": request.args.get("trimmed_instagram_hashtags"),
            "instagram_post_urls": request.args.get("instagram_post_urls"),
            "instagram_comments_counts": request.args.get("instagram_comments_counts"),
            "instagram_likes_counts": request.args.get("instagram_likes_counts"),
            "instagram_video_play_counts": request.args.get("instagram_video_play_counts"),
            "instagram_video_urls": request.args.get("video_urls"),
            "avg_comments": request.args.get("avg_comments"),
            "avg_likes": request.args.get("avg_likes"),
            "avg_video_play_counts": request.args.get("avg_video_play_counts"),
            "influencer_type": request.args.get("influencer_type"),
            "influencer_location": request.args.get("influencer_location"),
            "influencer_nationality": request.args.get("influencer_nationality"),
            "targeted_audience": request.args.get("targeted_audience"),
            "targeted_domain": request.args.get("targeted_domain"),
            "profile_type": request.args.get("profile_type"),
            "email_id": request.args.get("email"),
            "tiktok_id": request.args.get("tiktok_id"),
            "twitter_id": request.args.get("twitter_id"),
            "snapchat_id": request.args.get("snapchat_id"),
            "linkedin_id": request.args.get("linkedin_id"),
            "phone": request.args.get("phone"),
        }
        influencer_data['engagement_rate']= float((influencer_data.get("avg_likes",0) + influencer_data.get("avg_comments",0))/influencer_data.get("instagram_followers_count",1))
        influencer_data['estimated_reach']= float(0.20 * influencer_data.get("instagram_followers_count",0))
        export_influencer_data(influencer_data)
    except Exception as e:
        print(f"Error occurred while fetching influencer data from db: {e}")
        return {"status": "failed", "content": f"Error occurred while fetching influencer data from db"}


@app.route("/analyze_social_profile", methods=["GET"])
def analyze_social_profile_data():
    try:
        instagram_bio = request.args.get("instagram_bio")
        external_urls = request.args.get("external_urls")
        influencer_location = request.args.get("influencer_location")
        trimmed_instagram_caption = request.args.get("trimmed_instagram_caption")
        instagram_url = request.args.get("instagram_url")
        business_category_name = request.args.get("business_category_name")
        trimmed_instagram_hashtags = request.args.get("trimmed_instagram_hashtags")
        return profile_intelligence_engine(instagram_bio, external_urls, influencer_location, trimmed_instagram_caption, instagram_url, business_category_name, trimmed_instagram_hashtags)
    except Exception as e:
        print(f"Error occurred while analyzing the social profile: {e}")
        return {"status": "failed", "content": f"Error occurred while analyzing the social profile: {e}"}

@app.route("/get_influencer_data", methods=["GET"])
def get_influencer_data_from_db():
    try:
        user_query = request.args.get("user_query")
        brand_id = request.args.get("brand_id")
        brand_brief = "Stored in Google Docs"
        # brand_id = "rayban"
        # brand_brief = "looking for influencers in Dubai with more than 100k followers"
        # user_query = "select * from src_influencer_data limit 3"
        print(f"User Query: {user_query}, Brand ID: {brand_id}, Brand Brief: {brand_brief}")
        if user_query in ["", None] or brand_id in ["", None] or brand_brief in ["", None]:
            print(f"Invalid information passed. user_query : {user_query}")
            return {"status": "failed", "content": f"Invalid information passed. user_query : {user_query}"}
        return {"status": "success", "content": retrieve_data_from_db(user_query,brand_id,brand_brief)}
    except Exception as e:
        print(f"Error occurred while fetching influencer data from db: {e}")
        return {"status": "failed", "content": f"Error occurred while fetching influencer data from db"}

@app.route("/initiate_smart_query_engine", methods=["GET"])
def initiate_smart_query_engine():
    try:
        user_query = request.args.get("user_query")
        # user_query = "Give me top 10 influencers in Dubai with more than 100k followers" 
        if user_query in ["", None]:
            print(f"Invalid information passed. user_query : {user_query}")
            return {"status": "failed","content":f"Invalid information passed. user_query : {user_query}"}
        return convert_text_to_sql_v2(user_query)
        
    except Exception as e:
        print(f"Error occured while initiating smart query engine: {e}")
        return {"status":"failed","content":f"Error occured while initiating smart query engine"}

@app.route("/influencer_profile_scrape",methods=["GET"])
def influencer_profile_scraper():
    try:
        instagram_username = request.args.get("instagram_username")
        influencer_type = request.args.get("influencer_type")
        influencer_location = request.args.get("influencer_location")
        if instagram_username in ["",None]:
            raise
        return {"status":"passed","content":profile_scraper(instagram_username,influencer_type,influencer_location)}
    except Exception as e:
        print(f"Error occured while scraping influencer profile data : {e}")
        return {"status":"failed","content":f"Error occured while scraping profile data"}

@app.route("/influencer_post_scrape",methods=["GET"])
def influencer_post_scraper():
    try:
        instagram_username = request.args.get("instagram_username")
        posts_count = request.args.get("posts_count", type=int, default=10)
        followers_count = request.args.get("followers_count", type=int, default=0)
        if instagram_username in ["",None] or followers_count == 0:
            raise
        return {"status":"passed","content":post_scraper(instagram_username,posts_count,followers_count)}
    except Exception as e:
        print(f"Error occured while scraping influencer posts data : {e}")
        return {"status":"failed","content":f"Error occured while scraping posts data"}

@app.route("/combine_influencer_data",methods=["GET"])
def combine_influencer_data():
    try:
        data1 = request.args.get("data1")
        data2 = request.args.get("data2")
        combined_influencer_data = data1 | data2
        return {"status":"success","content":combined_influencer_data}
    except Exception as e:
        print(f"Error occured while combining influencer data : {e}")
        return {"status":"failed","content":f"Error occured while combining influencer data"}


@app.route("/add_influencer_to_db")
def store_influencer_data():
    try:
        influencer_data = request.args.get("influencer_data")
        if influencer_data in ["",None]:
            raise
        add_influencer_to_db(influencer_data)
        return {"status":"success","content":"Successfully added influencer data to the database"}
    except Exception as e:
        print(f"Error occured while adding influencer data to the database : {e}")
        return {"status":"failed","content":f"Error occured while adding influencer data to the database"}
    
    
@app.route("/influencer_data_collection",methods=["GET"])
def influencer_ingestion():
    try:
        instagram_username = request.args.get("instagram_username")
        posts_count = int(request.args.get("posts_count","1"))
        influencer_type = request.args.get("influencer_type")
        influencer_location = request.args.get("influencer_location")
        if instagram_username in ["",None]:
            raise
        data_collection(instagram_username,influencer_type,influencer_location,posts_count)
        return {"status":"successfully added data for influencers"}
    except Exception as e:
        print(f"Error occured while ingesting influencer data : {e}")
        return {"status":f"Error occured while collecting data"}

#######################################################

@app.route("/guideline_outreach", methods=["GET"])
def guideline_outreach():
    try:
        start_time = time.time()  # Start timer
        outreach_status = execute_outreach_sequence()
        end_time = time.time()  # End timer
        elapsed_minutes = (end_time - start_time) / 60  # Convert seconds to minutes
        print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
        return outreach_status
    except Exception as e:
        print(f"Error occured while generating the content for outreach: {e}")

@app.route("/guideline_generate", methods=["GET"])
def guideline_generate():
    try:
        start_time = time.time()  # Start timer
        generate_status = execute_generate_sequence()
        end_time = time.time()  # End timer
        elapsed_minutes = (end_time - start_time) / 60  # Convert seconds to minutes
        print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
        return generate_status
    except Exception as e:
        print(f"Error occured while generating the content for outreach: {e}")

# @app.route("/guideline_generate", methods=["GET"])
# def guideline_generate():
#     try:
#         generate_content_guideline()
#         return {"Status":"Successfully fetched organization list"}
#     except Exception as e:
#         print(f"Error occured while generating the content for outreach: {e}")

@app.route("/organization_list_enrichment", methods=["GET"])
def organization_list_enrichment():
    try:
        # print(f"Fetching organization list")
        # fetch_organization_domains(1)
        # print(f"Successfully fetched organization list")
        return {"Status":"Successfully fetched organization list"}
    except Exception as e:
        print(f"Error occured while fetching organization list: {e}")

@app.route("/guideline_data_sync", methods=["GET"])
def sync_data_guideline():
    try:
        print(f"Syncing data for guideline")
        influencer_marketing()
        # parse_contacts()
        return {"Status":"Data sync successful"}
    except Exception as e:
        return {"Status":f"Oops something wrong happened!: {e}"}

@app.route("/update_client_configuration_form", methods=["GET"])
def update_client_configuration_form():
    return  update_client_configuration()

@app.route("/update_client_onboarding_form", methods=["GET"])
def update_client_onboarding_form():
    return  update_client_onboarding()

@app.route("/add_leads_linkedin", methods=["GET"])
def add_leads_linkedin():
    try:
        # test url : 127.0.0.1:5000/linkedin_outreach?apollo_id=54a75889746869730aeb332c&campaign_id=316135&outreach_table_name=outreach_guideline
        linkedin_profile_url = request.args.get('linkedin_profile_url', type=str)
        apollo_id = request.args.get('apollo_id', type=str)
        cur_table_name = request.args.get('cur_table_name', type=str)
        photo_url = request.args.get('photo_url', type=str)
        campaign_id = request.args.get('campaign_id', type=str)
        recipient_full_name = request.args.get('recipient_full_name', type=str)
        recipient_email = request.args.get('recipient_email', type=str)
        recipient_company = request.args.get('recipient_company', type=str)
        linkedin_message = request.args.get('linkedin_message', type=str)
        linkedin_message2 = request.args.get('linkedin_message2', type=str)
        linkedin_subject = request.args.get('linkedin_subject', type=str)
        linkedin_connection_message = request.args.get('linkedin_connection_message', type=str)
        linkedin_leads_table_name = "linkedin_leads"
        data = {
            "thread_id":"NA",
            "apollo_id":apollo_id,
            "campaign_id":campaign_id,
            "full_name":recipient_full_name,
            "email":recipient_email,
            "linkedin_profile_url":linkedin_profile_url,
            "company":recipient_company,
            "message":linkedin_message,
            "message_2":linkedin_message2,
            "linkedin_subject":linkedin_subject,
            "linkedin_connection_message":linkedin_connection_message
        }
        export_to_airtable(data,linkedin_leads_table_name)
        return {"Status":"Successfully added the lead to the leads table"} 

    except Exception as e:
        return {"Status":f"Oops something wrong happened!: {e}"}

@app.route("/segregate_whatsapp_info", methods=["GET"])
def segregate_whatsapp_info():
    return process_whatsapp_data()

@app.route('/update_campaign_metrics',methods=['GET'])
def update_campaign_metrics():
    try:
        # test url 127.0.0.1:5000/update_campaign_metrics?campaign_id=316135
        campaign_id = request.args.get('campaign_id', type=str)
        status = update_linkedin_campaign_metrics(campaign_id)
        return {"Campaign Update Status":str(status)}
    except Exception as e:
        return {"Status":f"Oops something wrong happened!: {e}"}
        # execute_error_block(f"Error occured while client onboarding : {e}")

@app.route('/linkedin_outreach',methods=['GET'])
def linkedin_outreach():
    try:
        # test url : 127.0.0.1:5000/linkedin_outreach?apollo_id=54a75889746869730aeb332c&campaign_id=316135&outreach_table_name=outreach_guideline
        apollo_id = request.args.get('apollo_id', type=str)
        campaign_id = request.args.get('campaign_id', type=str)
        outreach_table_name = request.args.get('outreach_table_name', type=str)
        print(f"apollo_id: {apollo_id}, campaign_id: {campaign_id}, outreach_table_name: {outreach_table_name}")
        status = add_lead_leadsin(apollo_id,campaign_id,outreach_table_name)
        return {"Status":str(status)} 

    except Exception as e:
        return {"Status":f"Oops something wrong happened!: {e}"}
        # execute_error_block(f"Error occured while client onboarding : {e}")

@app.route('/fetch_records', methods=['GET'])
def fetch_records():
    try:
        # Get `inputed_created_time` from query parameters
        inputed_created_time = request.args.get("inputed_created_time")
        
        if not inputed_created_time:
            return jsonify({"error": "Missing inputed_created_time parameter"}), 400
        
        try:
            # Ensure the input datetime is correctly formatted
            datetime.datetime.strptime(inputed_created_time, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            return jsonify({"error": "Invalid datetime format. Use YYYY-MM-DD HH:MM:SS.ssssss"}), 400

        # Convert input time to Airtable's required ISO 8601 format
        inputed_created_time_iso = datetime.datetime.strptime(inputed_created_time, "%Y-%m-%d %H:%M:%S.%f").isoformat()

        # Correct filter formula to compare with `created_time` field
        filter_formula = f"{{created_time}} > '{inputed_created_time_iso}'"

        params = {
            "filterByFormula": filter_formula,
            "fields[]": ["apollo_id", "recipient_first_name", "created_time"]
        }

        response = requests.get(AIRTABLE_URL, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch data", "details": response.text}), 500

        data = response.json()
        records = [
            {
                "apollo_id": str(record["fields"].get("apollo_id", "")),  # Ensure long text is handled properly
                "recipient_first_name": str(record["fields"].get("recipient_first_name", "")),  # Convert to string
                "created_time": record["fields"].get("created_time", "")
            }
            for record in data.get("records", [])
        ]

        return jsonify({"records": records})
    except Exception as e:
        execute_error_block(f"Error occurred while fetching latest records from the outreach table for LinkedIn: {e}")

@app.route("/testing_connection", methods=["GET"])
def testing_connection():
    try:
        print('------------Started Testing --------------')
        # icp_url = generate_apollo_url(client_id = "cl_berkleys_homes",page_number=1,records_required=2,organization="creativemediahouse.ae")
        return {'Status':"Hello World"}
    except Exception as e:
        execute_error_block(f"Error occured while testing. {e}")

@app.route('/get_phone_numbers', methods=['GET'])
def retrieve_phone_numbers():
    try:
        apollo_id = request.args.get('apollo_id', type=str)
        cur_table_name = request.args.get('cur_table_name', type=str)
        outreach_table_name = request.args.get('outreach_table_name', type=str)
        print(f"apollo_id: {apollo_id}, cur_table_name: {cur_table_name}, outreach_table_name: {outreach_table_name}")
        phone = phone_number_updation(apollo_id,cur_table_name,outreach_table_name)
        return {"phone":phone}
    except Exception as e:
        execute_error_block(f"Error occured while fetching phone numbers. {e}")

@app.route('/apollo_webhook', methods=['POST'])
def apollo_webhook():
    try:
        def get_sanitized_phone_number(data):
            try:
                return data.get('people', [{}])[0].get('phone_numbers', [{}])[0].get('sanitized_number', 'NA')
            except (IndexError, KeyError, TypeError):
                return "NA"
        
        received_data = request.get_json()
        print("Received data:", received_data)
        apollo_table = "apollo_webhook"
        phone = get_sanitized_phone_number(received_data)
        apollo_id = str(received_data['people'][0]['id'])
        data = {
            "apollo_id":apollo_id,
            "response":str(received_data),
            "phone":str(phone)
        }
        add_apollo_webhook_info(data,apollo_table)
        return jsonify({"status": "success", "message": "Data received"}), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/data_sanitization", methods=["GET"])
def initialize_data_sanitization():
    try:
        client_id = request.args.get('client_id', type=str)
        if client_id in ["",None]:
            print(f"Invalid information passed. client_id : {client_id}")
            return {"Status":f"Invalid information passed. client_id : {client_id}"}
        print(f"Fetched parameters-> client_id : {client_id}")
        response = fetch_and_update_data(client_id)
        return response
    except Exception as e:
        execute_error_block(f"Error occured while initializing data sanitization module {e}")

@app.route("/web_analysis", methods=["GET"])
def analyze_website():
    try:
        client_id = request.args.get('client_id', type=str)
        website_url = request.args.get('website_url', type=str)
        apollo_tags = web_analysis(website_url,client_id)
        return {"apollo_tags":apollo_tags}
    except Exception as e:
        execute_error_block(f"Error occured while initializing analyzing website module {e}")

@app.route("/generate_lead_magnet", methods=["GET"])
def generate_lead_magnet():
    try:
        # generate_lead_magnet?linkedin_url=https://www.linkedin.com/in/nithin-paul-7063b1183/&email_id=sravzone@gmail.com
        linkedin_url = request.args.get('linkedin_url', type=str)
        email_id = request.args.get('email_id', type=str)
        print(f"Linkedin url: {linkedin_url}")
        print(f"Email id: {email_id}")
        response = generate_lead_magnet_pdf(email_id,linkedin_url)
        print(response)
        return response
    except Exception as e:
        execute_error_block(f"Error occured while generating lead magnet {e}")

@app.route("/update-email-opens", methods=["GET"])
def update_email_opens_clicked():
    try:
        response = update_email_opens()
        return response
    except Exception as e:
        execute_error_block(f"Error occured while counting email opened and email clicked {e}")
# # test datasanitization
# @app.route("/test_sanitize_new", methods=["GET"])
# def test_sanitize_new():
#     try:
#         response = test_sanitize()
#         return response
#     except Exception as e:
#         execute_error_block(f"Error occured while counting email opened and email clicked {e}")
#         @app.route("/test_sanitize_new", methods=["GET"])



@app.route("/test_sanitize_psql", methods=["POST"])
def test_sanitize_psql():
    try:
        data = request.get_json(force=True)

        client_id = data.get("client_id")
        data_dict = data.get("data")  # <-- FIXED HERE

        if not client_id or not data_dict:
            return jsonify({"error": "Missing client_id or data"}), 400

        response = sanitize_data(client_id, data_dict)
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500




@app.route("/test_chroma",methods=["GET"])
def test_chroma():
    try:
        status = chroma_db_testing()
        return {"Status":status}
    except Exception as e:
        print(f"Error occured while testing chroma db sqlite version")

@app.route("/test_sanitization", methods=["GET"])
def test_sanitization():
    try:
        client_id="plot_taippa"
        response=fetch_and_update_data(client_id)
        return {"Status":"Testing sanitization successful"}
    except Exception as e:
        print(f"Exception occured while testing sanitization module : {e}")

@app.route("/fetch-inbox-details", methods=["GET"])
def fetch_inbox_details_full():
    try:
        response = fetch_inbox_details()
        return response
    except Exception as e:
        execute_error_block(f"Error occured while fetching inbox details : {e}")

@app.route("/client_onboarding", methods=["GET"])
def client_onboarding():
    try:
        # 127.0.0.1:5000/client_onboarding?client_id=upgrade&website_url=https://www.upgrade-now.com/b2b-sales-agency-en-2&recipient_email=sravzone@gmail.com&recipient_name=Srav&password=upgrade123
        start_time = time.time()  # Start timer
        print(f"\n\n------------- Client Onboarding Process Started for client_id-----------------\n\n")
        client_id = request.args.get('client_id', type=str)
        website_url = request.args.get('website_url', type=str)
        password = request.args.get('password', type=str)
        recipient_name = request.args.get('recipient_name', 'Customer')
        recipient_email = request.args.get('recipient_email')
        if client_id in ["",None] or website_url in ["",None] or password in ["",None] or recipient_email in ["",None] or recipient_name in ["",None]:
            print(f"Invalid information passed. client_id : {client_id}, website_url: {website_url}, recipient_email {recipient_email}, password: {password}, recipient_name: {recipient_name}")
            return {"Status":f"Invalid information passed. client_id : {client_id}, website_url: {website_url}"}
        print(f"Fetched parameters-> client_id : {client_id}, website_url: {website_url}, recipient_email {recipient_email}, password: {password}, recipient_name: {recipient_name}")
        src_table, cur_table, outreach_table = create_client_tables(client_id)
        print(f"------ Client tables created for client_id : {client_id} -------------")
        add_client_tables_info(client_id,src_table,cur_table,outreach_table)
        print(f"------ Added client tables info to the airtable for client_id : {client_id} -------------")
        status = generate_icp(client_id,website_url)
        print(f"------ Successfully generated ICP and stored client details in Vector database: {client_id} -------------")
        print(f"\n\n------------Sending Email to Client for credentials --------------------\n\n")
        login_email_sender(recipient_name,recipient_email,client_id,password)
        end_time = time.time()  # End timer
        elapsed_minutes = (end_time - start_time) / 60  # Convert seconds to minutes
        print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
        print("\n\n=======================Client onboarding completed successfuly======================\n\n")
        return {"Status":"Client onboarding process completed" if status else "Client onboarding process failed"}
    except Exception as e:
        return {"Status":f"Client onboarding process failed: {e}"}

@app.route("/client_onboarding_test", methods=["GET"])
def client_onboarding_test():
    try:
        start_time = time.time()  # Start timer
        print(f"\n\n------------- Client Onboarding Process Started for client_id-----------------\n\n")
        client_id = request.args.get('client_id', type=str)
        website_url = request.args.get('website_url', type=str)
        password = request.args.get('password', type=str)
        recipient_name = request.args.get('recipient_name', 'Customer')
        recipient_email = request.args.get('recipient_email')
        if client_id in ["",None] or website_url in ["",None] or password in ["",None] or recipient_email in ["",None] or recipient_name in ["",None]:
            print(f"Invalid information passed. client_id : {client_id}, website_url: {website_url}, recipient_email {recipient_email}, password: {password}, recipient_name: {recipient_name}")
            return {"Status":f"Invalid information passed. client_id : {client_id}, website_url: {website_url}"}
        print(f"Fetched parameters-> client_id : {client_id}, website_url: {website_url}, recipient_email {recipient_email}, password: {password}, recipient_name: {recipient_name}")
        src_table, cur_table, outreach_table = create_client_tables(client_id)
        print(f"------ Client tables created for client_id : {client_id} -------------")
        add_client_tables_info(client_id,src_table,cur_table,outreach_table)
        print(f"------ Added client tables info to the airtable for client_id : {client_id} -------------")
        status = generate_icp(client_id,website_url)
        print(f"------ Successfully generated ICP and stored client details in Vector database: {client_id} -------------")
        print("\n\n--------Started Data Sync ---------\n\n")
        trigger_pipeline()
        print("\n\n--------Completed Data Sync ---------\n\n")
        print("Client onboarding successful")
        print(f"\n\n------------Sending Email to Client for credentials --------------------\n\n")
        login_email_sender(recipient_name,recipient_email,client_id,password)
        end_time = time.time()  # End timer
        elapsed_minutes = (end_time - start_time) / 60  # Convert seconds to minutes
        print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
        print("\n\n=======================Client onboarding completed successfuly======================\n\n")
        return {"Status":"Client onboarding process completed" if status else "Client onboarding process failed"}
    except Exception as e:
        return {"Status":f"Client onboarding process failed: {e}"}
    
@app.route("/demo_test", methods=["GET"])
def demo_test():
    try:
        linkedin_url = request.args.get('linkedin_url', type=str)
        client_id = request.args.get('client_id', type=str)
        # linkedin_url = "https://www.linkedin.com/in/isravanbr/"
        # client_id = 'berkleys_homes'
        outreach_table = 'outreach_demo'
        status = run_demo_pipeline(linkedin_url,client_id,outreach_table)
        return {"Status":"Demo execution successful" if status else "Failed running demo pipeline"} 

    except Exception as e:
        return {"Status":f"Oops something wrong happened!: {e}"}
        # execute_error_block(f"Error occured while client onboarding : {e}")

# @app.route("/scheduled_data_sync_generic", methods=["GET"])
# def scheduled_data_sync_generic():
#     try:
#         start_time = time.time()  
#         status = trigger_pipeline_generic()
#         end_time = time.time()  
#         elapsed_minutes = (end_time - start_time) / 60
#         print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
#         return {"Status":"Successful"}
#     except Exception as e:
#         print(f"Exception occured during scheduled data sync: {e}")
#         execute_error_block(f"Exception occured during scheduled data sync: {e}")

# @app.route("/scheduled_data_sync", methods=["GET"])
# def scheduled_data_sync():
#     try:
#         start_time = time.time()  # Start timer
#         status = trigger_pipeline_custom()
#         end_time = time.time()  # End timer
#         elapsed_minutes = (end_time - start_time) / 60  # Convert seconds to minutes
#         print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
#         return {"Status":"Successful"}
#     except Exception as e:
#         print(f"Exception occured during scheduled data sync: {e}")
#         execute_error_block(f"Exception occured during scheduled data sync: {e}")

# 127.0.0.1:8080/scheduled_data_sync_custom?client_id=guideline
@app.route("/scheduled_data_sync_custom", methods=["GET"])
def scheduled_data_sync_custom():
    try:
        # /scheduled_data_sync_custom?client_id=possible_event
        start_time = time.time()  # Start timer
        client_id = request.args.get('client_id', type=str)
        if client_id in ["",None]:
            print(f"Invalid information passed. client_id : {client_id}")
            return {"Status":f"Invalid information passed. client_id : {client_id}"}
        status = trigger_custom_pipeline(client_id)
        end_time = time.time()  # End timer
        elapsed_minutes = (end_time - start_time) / 60  # Convert seconds to minutes
        print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
        return {"Status":"Successful"}
    except Exception as e:
        print(f"Exception occured during scheduled data sync: {e}")
        execute_error_block(f"Exception occured during scheduled data sync: {e}")

@app.route("/run_pipeline_check", methods=["GET"])
def run_pipeline_check():
    try:
        print(f"Testing pipeline run")
        status = "True"
        # print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
        return {"Status":"Test pipeline execution successful"}
    except Exception as e:
        return {"Status":f"Oops something wrong happened!: {e}"}

@app.route("/lead_magnet_generate")
def lead_magnet_generate():
    try:
        # linkedin_url = "http://www.linkedin.com/in/galeapatricia"
        # linkedin_url = "http://www.linkedin.com/in/akshay-patil-digital"
        linkedin_url = request.args.get('linkedin_url', type=str)
        user_id = "sravan.workemail@gmail.com"
        print(f"Testing lead magnet")
        generate_lead_magnet_pdf(user_id,linkedin_url)
        return test_run()
    except Exception as e:
        print(f"Error occured while testing lead magnet: {e}")

#Email dashboard 
@app.route("/get_profile_picture_dashboard/<username>", methods=["GET"])
def get_profile_picture_dashboard(username):
    # username = request.args.get('username', type=str)
    return   get_profile_picture(username)

@app.route("/get_recent_leads_dashboard/<username>", methods=["GET"])
def get_recent_leads_dashboard(username):
    data, status = fetch_recent_leads_from_db(username)
    return jsonify(data), status

@app.route("/get_statistics_dashboard", methods=["GET"])
def get_statistics_dashboard():
    username = request.args.get("username")
    field = request.args.get("field")

    if not username or not field:
        return jsonify({"error": "Missing 'username' or 'field' parameter"}), 400

    value = fetch_metric_value(username, field)
    return jsonify({"value": value}), 200

@app.route("/get_booking_count_dashboard", methods=["GET"])
def get_booking_count_dashboard():
    username = request.args.get("username", default=None)
    
    if not username:
        # If 'username' is missing, use 0 as the value
        value = 0
    else:
        value = get_booking_count(username)
    
    return jsonify({"value": value}), 200

@app.route("/get_email_sent_chart_dashboard/<username>", methods=["GET"])
def get_email_sent_chart_dashboard(username):
    return email_sent_chart(username)

@app.route("/get_campaign_details_dashboard/<username>", methods=["GET"])
def get_campaign_details_dashboard(username):
    return get_campaign_details(username)


@app.route("/get_recent_replies_dashboard", methods=["GET"])
def get_recent_replies_dashboard():
    user_id = request.args.get("username")  # assuming username = client_id
    if not user_id:
        return {"error": "Username is required"}, 400

    try:
        data = fetch_leads(user_id)  # Pass user_id to fetch_leads
        return {"data": data}, 200
    except Exception as e:
        return {"error": str(e)}, 500
    

@app.route("/get_user_campaigns_dashboard", methods=["GET"])
def get_user_campaigns_dashboard():
    user_id = request.args.get("username")  # assuming username = client_id
    if not user_id:
        return {"error": "Username is required"}, 400

    try:
        data = get_user_campaigns(user_id)  # <-- Pass user_id explicitly
        return {"data": data}, 200
    except Exception as e:
        return {"error": str(e)}, 500

    
@app.route("/get_campaign_metrics_dashboard", methods=["POST"])
def get_campaign_metrics_dashboard():
    data = request.get_json()
    campaign_id = data.get("campaign_id")

    if not campaign_id:
        return {"error": "Campaign id is required"}, 400

    try:
        metrics = get_campaign_metrics(campaign_id)
        return {"data": metrics}, 200
    except Exception as e:
        return {"error": f"Error fetching campaign metrics: {str(e)}"}, 500

@app.route("/get_lead_details_dashboard", methods=["GET"])
def get_lead_details_dashboard():
    user_id = request.args.get("username")
    email = request.args.get("email")

    if not user_id or not email:
        return {"error": "Username or Email is required"}, 400

    try:
        data = get_lead_details(user_id, email)
        return {"data": data}, 200
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/linkedin_metrics_table_dashboard", methods=["GET"])
def linkedin_metrics_table_dashboard():
    client_id = request.args.get("client_id")   # ← keep the name consistent
    if not client_id:
        return jsonify({"error": "client_id is required"}), 400

    try:
        data = get_linkedin_metrics(client_id)
        return jsonify({"data": data}), 200
    except ValueError as ve:
        # custom “not found” error from helper
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        # anything else = 500
        return jsonify({"error": str(e)}), 500
    
# @app.route("/linkedin_campaign_details_dashboard", methods=["GET"])
# def linkedin_campaign_details_dashboard():
#     username = request.args.get("username")
#     if not username:
#         return jsonify({"error": "username is required"}), 400

#     try:
#         data = get_linkedin_campaign_details(username)
#         return jsonify({"data": data}), 200
#     except ValueError as ve:
#         return jsonify({"error": str(ve)}), 404
#     except Exception as e:
#         return jsonify({"error": "Internal server error"}), 500
@app.route("/linkedin_campaign_details_dashboard/<username>", methods=["GET"])
def linkedin_campaign_details_dashboard(username):
    return get_linkedin_campaign_details(username)

@app.route("/get_linkedin_statistics_dashboard", methods=["GET"])
def get_linkedin_statistics_dashboard():
    username = request.args.get("username")
    field = request.args.get("field")

    if not username or not field:
        return jsonify({"error": "Missing 'username' or 'field' parameter"}), 400

    data = get_linkedin_statistics(username, field)

    if data is None:
        return jsonify({"error": "No campaign found for user"}), 404

    return jsonify(data), 200

@app.route("/get_linkedin_replies_dashboard", methods=["GET"])
def get_linkedin_replies_dashboard():
    username = request.args.get("username")
    
    if not username:
        return jsonify({"error": "Missing 'username' parameter"}), 400

    data = get_linkedin_replies(username)

    if data is None:
        return jsonify({"error": "Failed to fetch leads"}), 500

    return jsonify({"leads": data}), 200

@app.route("/get_linkedin_leads_dashboard", methods=["GET"])
def get_linkedin_leads_dashboard():
    username = request.args.get("username")
    
    if not username:
        return jsonify({"error": "Missing 'username' parameter"}), 400

    data, status = get_linkedin_leads_by_username(username)
    return jsonify(data), status

    return jsonify({"leads": data}), 200
@app.route("/fetch_airtable_data_and_create_csv", methods=["GET"])
def trigger_csv_generation():
    return generate_csv_and_send_email()



@app.route("/test_db",methods=["GET"])
def connect_db():
    try:
        test()
        return {"Status":"Testing completed"}
    except Exception as e:
        print(f"Error occured while testing connection")

#Make Scenarios
@app.route("/run_linkedin_message_sent_tracker", methods=["GET"])
def run_linkedin_message_sent_tracker():
    try:
        thread_id = request.args.get("thread_id", default=None)
        campaign_name = request.args.get("campaign_name", default=None)
        linkedin_profile_url = request.args.get("linkedin_profile_url", default=None)
        full_name = request.args.get("full_name", default=None)
        email = request.args.get("email", default=None)
        picture = request.args.get("picture", default=None)
        data = {
            "thread_id": thread_id,
            "campaign_name": campaign_name,
            "linkedin_profile_url": linkedin_profile_url,
            "full_name": full_name,
            "email": email,
            "picture": picture
        }
        linkedin_message_sent_tracker(data)
        return {"status": "success", "message": "Testing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route("/run_linkedin_invite_sent_tracker", methods=["GET"])
def run_linkedin_invite_sent_tracker():
    try:
        thread_id = request.args.get("thread_id", default=None)
        campaign_name = request.args.get("campaign_name", default=None)
        linkedin_profile_url = request.args.get("linkedin_profile_url", default=None)
        full_name = request.args.get("full_name", default=None)
        email = request.args.get("email", default=None)
        picture = request.args.get("picture", default=None)
        data = {
            "thread_id": thread_id,
            "campaign_name": campaign_name,
            "linkedin_profile_url": linkedin_profile_url,
            "full_name": full_name,
            "email": email,
            "picture": picture
        }
        linkedin_invite_sent_tracker(data)
        # linkedin_invite_sent_tacker()
        return {"status": "success", "message": "Testing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500  
     
@app.route("/run_linkedin_invite_accepted_tracker", methods=["GET"])
def run_linkedin_invite_accepted_tracker():
    try:
        thread_id = request.args.get("thread_id", default=None)
        campaign_name = request.args.get("campaign_name", default=None)
        linkedin_profile_url = request.args.get("linkedin_profile_url", default=None)
        full_name = request.args.get("full_name", default=None)
        email = request.args.get("email", default=None)
        picture = request.args.get("picture", default=None)
        data = {
            "thread_id": thread_id,
            "campaign_name": campaign_name,
            "linkedin_profile_url": linkedin_profile_url,
            "full_name": full_name,
            "email": email,
            "picture": picture
        }
        linkedin_invite_accepted_tracker(data)
        # linkedin_invite_accepted_tacker()
        return {"status": "success", "message": "Testing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500   

@app.route("/run_linkedin_ai_response_tracker", methods=["GET"])
def run_linkedin_ai_response_tracker():
    try:
        thread_id = request.args.get("thread_id", default=None)
        campaign_name = request.args.get("campaign_name", default=None)
        linkedin_profile_url = request.args.get("linkedin_profile_url", default=None)
        full_name = request.args.get("full_name", default=None)
        email = request.args.get("email", default=None)
        picture = request.args.get("picture", default=None)
        response_message = request.args.get("response_message", default=None)
        sentiment = request.args.get("response_message", sentiment=None)

        data = {
            "thread_id": thread_id,
            "campaign_name": campaign_name,
            "linkedin_profile_url": linkedin_profile_url,
            "full_name": full_name,
            "email": email,
            "picture": picture,
            "response_message": response_message,
            "sentiment": sentiment
        }

        linkedin_ai_response_tracker(data)
        return {"status": "success", "message": "Testing completed"}

    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route("/send_generic_email", methods=["GET"])
def send_generic_email():
    try:
        html_content = """
            <p>Hi Mag,</p>
            <p>We've received a response for the <strong>"Guideline Middle East"</strong> campaign via LinkedIn.</p>
            <h4>Lead Details:</h4>
            <ul>
            <li><strong>Name:</strong> John Doe</li>
            <li><strong>LinkedIn:</strong> https://linkedin.com/in/johndoe</li>
            <li><strong>Message:</strong> "Looking forward to speaking."</li>
            </ul>
            <br>
            This is an automated message generated by our lead capture system.
            <br>
            <p>Best,<br>Team Generate</p>
            """

        send_html_email(
            to_email='shiblashilu@gmail.com',
            subject='New Lead Response - Guideline Middle East',
            html_content=html_content,
            cc_emails=['sravan@taippa.com', 'shilusaifshilu@gmail.com.com']
        )
        return {"status": "success", "message": "email Sent Successfully"}

    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
    
@app.route("/run_email_sent_tracker", methods=["GET"])
def run_email_sent_tracker():
    try:
        
        campaign_id = request.args.get("Campaign ID", default=None)
        lead_email = request.args.get("linkedin_profile_url", default=None)
        campaign_name = request.args.get("Campaign Name", default=None)
        personalization = request.args.get("personalization", default=None)
        FollowUpEmail = request.args.get("FollowUpEmail", default=None)
        step = request.args.get("step", default=None)
        

        data = {
            "Campaign ID": campaign_id,
            "Lead Email": lead_email,
            "Campaign Name": campaign_name, 
            "personalization": personalization,
            "FollowUpEmail" : FollowUpEmail,
            "step": step, 
        }

        email_sent_tracker(data)
        return {"status": "success", "message": "Testing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
    
@app.route("/run_email_post_response_tracker", methods=["GET"])
def run_email_post_response_tracker():
    try:
       
        email_post_response_tracker()
        return {"status": "success", "message": "Testing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route("/run_booking_meeting_tracker", methods=["GET"])
def run_booking_meeting_tracker():
    try:
        # Text_Content = request.args.get("Text_Content", default=None),
        email= request.args.get("Invitee_email", default=None),        
        full_name= request.args.get("Invitee", default=None),
        booking_date_time= request.args.get("Event_date", default=None),
        event_type= request.args.get("event_type", default=None),
        phone= request.args.get("phone", default=None),
        
        
        data = {
            "email": email,            
            "full_name": full_name,
            "booking_date_time": booking_date_time,
            "event_type":event_type,
            "phone": phone
        }

        booking_meeting_tracker(data)
        return {"status": "success", "message": "Booking tracker completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
    
@app.route("/run_booking_meeting_form_tracker", methods=["POST"])
def run_booking_meeting_form_tracker():
    try:
        return booking_meeting_form_tracker()
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
# # Optional: Route to trigger index.html from a custom endpoint
# @app.route("/influencer_data_view", methods=["GET"])
# def run_influencer_data_view():
#     try:
#         return index()
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500

    
if __name__ == '__main__':
#   app.run(debug=True,use_reloader=False)
#   app.run(port=8001) 
  app.run(host="127.0.0.1",debug=True, port=5050)
