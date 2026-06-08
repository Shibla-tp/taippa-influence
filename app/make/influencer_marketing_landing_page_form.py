from flask import request, jsonify
from pyairtable import Api
import os
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS,APIFY_API_TOKEN
# Airtable Config

TABLE_NAME = "registered_influencers"

# Airtable Client
api = Api(AIRTABLE_API_KEY)
table = api.table(AIRTABLE_BASE_ID, TABLE_NAME)

def influencer_form_tracker():
    try:
        data = request.get_json()
        print("🔹 Incoming Data:", data)

        if not data:
            return jsonify({"error": "No data received"}), 400

        contact = data.get("data", {}).get("contact", {})
        fields = contact.get("fields", {})
        funnel_info = data.get("data", {}).get("funnel_step", {})
        funnel_name = funnel_info.get("funnel", {}).get("name", "")

        email = contact.get("email")
        first_name = fields.get("first_name", "")
        surname = fields.get("surname", "")
        company_name = fields.get("company_name", "")  # spelling fixed
        snap_url = fields.get("city", "")
        fb_url = fields.get("neighborhood", "")
        twitter_url= fields.get("street_address", "")
        tiktok_url = fields.get("state", "")
        phone = fields.get("phone_number")

        if not email or not first_name or not phone:
            return jsonify({"error": "Missing email, name, or phone"}), 400

        # Check if record exists
        
        records = table.all(formula=f"{{email}} = '{email}'")
        if not records:
            print(f"➕ Creating new record for {email}")
            table.create({
                "first_name": first_name,
                "email": email,
                "instagram_handle_name": surname,
                "tiktok_handle_name": company_name,
                "snap_handle_name": snap_url,
                "fb_handle_name": fb_url,
                "twitter_handle_name": twitter_url,
                "tiktok_handle_name": tiktok_url,
                "phone_number": phone
            })
        else:
            print(f"✅ Record already exists for {email}, skipping.")

        return jsonify({"status": "success", "message": "Data saved to Airtable"}), 200

    except Exception as e:
        print(f"❌ Error processing request: {e}")
        return jsonify({"error": str(e)}), 500
