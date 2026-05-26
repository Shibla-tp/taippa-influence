from flask import request, jsonify
from pyairtable import Api
import os

# Airtable setup
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY", "your_airtable_api_key")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "your_base_id")
AIRTABLE_TABLE_NAME = "booking_records"

api = Api(AIRTABLE_API_KEY)
table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

def lead_magnet_influencer_form():
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
        phone = fields.get("phone_number")

        full_name = f"{first_name} {surname}".strip()
        client_id = funnel_name.lower().replace(" ", "_") or "taippa_marketing"

        if not email or not full_name or not phone:
            return jsonify({"error": "Missing email, name, or phone"}), 400

        # Create new Airtable record (always)
        airtable_record = {
            "email": email,
            "client_id": client_id,
            "full_name": full_name,
            "phone_number": phone
        }

        print(f"➕ Creating new Airtable row for: {email}")
        table.create(airtable_record)

        return jsonify({"status": "success", "message": "New row created in Airtable"}), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500
