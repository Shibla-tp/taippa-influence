from db.db_ops import db_manager
from flask import request, jsonify

def booking_meeting_form_tracker():
    try:
        # Get JSON payload from the incoming request
        data = request.get_json()
        print("🔹 Incoming Data:", data)

        if not data:
            return jsonify({"error": "No data received"}), 400

        # Extract core info
        contact = data.get("data", {}).get("contact", {})
        fields = contact.get("fields", {})
        funnel_info = data.get("data", {}).get("funnel_step", {})
        funnel_name = funnel_info.get("funnel", {}).get("name", "")

        # Parse required values
        email = contact.get("email")
        first_name = fields.get("first_name", "")
        surname = fields.get("surname", "")
        phone = fields.get("phone_number")

        full_name = f"{first_name} {surname}".strip()
        client_id = funnel_name.lower().replace(" ", "_") or "taippa_marketing"

        # Validate
        if not email or not full_name or not phone:
            return jsonify({"error": "Missing email, name, or phone"}), 400

        # Prepare record for update
        inbox_record = {
            "email": email,                  # must match the primary_key_col
            "client_id": client_id,
            "full_name": full_name,
            "phone_number": phone
        }

        print(f"🔄 Updating record for: {email}")
        db_manager.update_multiple_fields(
            table_name="booking_records",
            record=inbox_record,
            primary_key_col="email"
        )

        return jsonify({"status": "success", "message": "Booking data updated"}), 200

    except Exception as e:
        print(f"❌ Error processing request: {e}")
        return jsonify({"error": str(e)}), 500
