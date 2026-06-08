from flask import Flask, jsonify
import requests
import logging
import re
from datetime import datetime
import pytz

# ✅ Configure logging
logging.basicConfig(level=logging.INFO)

# ✅ Airtable Credentials
AIRTABLE_API_KEY = "patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3"
AIRTABLE_BASE_ID = "app5s8zl7DsUaDmtx"

# ✅ Table Names
WHATSAPP_TABLE = "whatsapp_table"
OUTREACH_TABLE = "cur_guideline"
DASHBOARD_INBOX_TABLE = "dashboard_inbox"

# ✅ API URLs
WHATSAPP_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{WHATSAPP_TABLE}"
OUTREACH_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{OUTREACH_TABLE}"
DASHBOARD_INBOX_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{DASHBOARD_INBOX_TABLE}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

LOCAL_TZ = pytz.timezone("Asia/Dubai")  # Adjust based on your region

def format_created_time(iso_time):
    """Convert Airtable 'Created' time from UTC to local time in MM/DD/YYYY HH:MM format."""
    if not iso_time:
        return "N/A"

    try:
        # Convert from UTC to local time
        dt_utc = datetime.fromisoformat(iso_time.replace("Z", "+00:00")).astimezone(pytz.utc)  # Parse as UTC
        dt_local = dt_utc.astimezone(LOCAL_TZ)  # Convert to local time

        return dt_local.strftime("%m/%d/%Y %I:%M %p")  # Convert to MM/DD/YYYY HH:MM AM/PM
    except ValueError:
        logging.error(f"❌ Invalid created time format: {iso_time}")
        return "N/A"

def format_reply_time(reply_time):
    """Convert long text reply_time to MM/DD/YYYY HH:MM format."""
    if not reply_time or reply_time == "N/A":
        return "N/A"
    
    # Extract datetime from text
    match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', reply_time)  
    if match:
        try:
            # Convert to datetime object in UTC
            dt_utc = datetime.fromisoformat(match.group(1)).replace(tzinfo=pytz.utc)
            
            # Convert to local time
            dt_local = dt_utc.astimezone(LOCAL_TZ)
            
            return dt_local.strftime("%m/%d/%Y %I:%M %p")  # MM/DD/YYYY HH:MM AM/PM format
        except ValueError:
            logging.error(f"❌ Invalid date format in reply_time: {reply_time}")
            return "N/A"
    
    logging.error(f"❌ No valid date found in reply_time: {reply_time}")
    return "N/A"


def record_exists(phone, message):
    """Check if a record with the same phone and message already exists in dashboard_inbox."""
    if not phone or not message:
        return False  

    normalized_phone = phone.strip().lstrip("+")  
    filter_formula = f"AND(phone_number=\"{normalized_phone}\", reply_message_1=\"{message}\")"
    query_url = f"{DASHBOARD_INBOX_URL}?filterByFormula={filter_formula}"

    logging.info(f"🛠️ Checking duplicates: {query_url}")
    response = requests.get(query_url, headers=HEADERS)

    if response.status_code == 200:
        records = response.json().get("records", [])
        logging.info(f"✅ Found {len(records)} duplicate(s).")
        return len(records) > 0  
    else:
        logging.error(f"❌ Failed to check duplicates: {response.text}")
        return False  

def process_whatsapp_data():
    """Fetch WhatsApp messages, match phone_number to email and photo_url, and save to dashboard_inbox."""
    try:
        # ✅ Fetch outreach data (phone-to-email and photo mapping)
        outreach_response = requests.get(OUTREACH_URL, headers=HEADERS)
        outreach_response.raise_for_status()
        outreach_records = outreach_response.json().get("records", [])

        phone_data_map = {
            record["fields"].get("phone", "").strip(): {
                "email": record["fields"].get("email", "").strip(),
                "photo_url": record["fields"].get("photo_url", "").strip()
            }
            for record in outreach_records if "phone" in record["fields"]
        }
        logging.info(f"✅ Fetched {len(outreach_records)} outreach records.")

        # ✅ Fetch WhatsApp messages
        whatsapp_response = requests.get(WHATSAPP_URL, headers=HEADERS)
        whatsapp_response.raise_for_status()
        whatsapp_records = whatsapp_response.json().get("records", [])

        if not whatsapp_records:
            logging.warning("⚠️ No WhatsApp messages found.")
            return jsonify({"error": "No WhatsApp messages found"}), 404
        
        logging.info(f"✅ Fetched {len(whatsapp_records)} WhatsApp records.")

        # ✅ Process each WhatsApp record
        saved_count = 0
        for record in whatsapp_records:
            record_id = record["id"]
            fields = record.get("fields", {})

            phone_number = fields.get("phone_number", "").strip()
            last_message = fields.get("last_message", "").strip()
            name = fields.get("Name", "N/A").strip()
            whatsapp_sentiment = fields.get("whatsapp_sentiment", "N/A").strip() 
            reply_time_raw = fields.get("reply_time", "N/A").strip()  
            created_time = format_created_time(fields.get("Created", ""))

            # ✅ Log raw reply_time for debugging
            logging.info(f"🔍 Raw reply_time: {reply_time_raw}")

            # ✅ Format reply_time
            reply_time = format_reply_time(reply_time_raw)

            logging.info(f"📅 Formatted reply_time: {reply_time}")

            # ✅ Split last_message using regex
            matches = re.findall(r"------------------------\s*(.*?)\s*------------------------\s*(.*)", last_message, re.DOTALL)
            reply_message_1 = matches[0][0].strip() if matches else "N/A"
            reply_message_2 = matches[0][1].strip() if matches else "N/A"

            # ✅ Get email and photo_url from outreach table
            contact_info = phone_data_map.get(phone_number, {})
            email = contact_info.get("email", "N/A")
            profile_picture_url = contact_info.get("photo_url", "")

            # ✅ Check for duplicates before saving
            if record_exists(phone_number, reply_message_1):
                logging.info(f"❌ Duplicate found, skipping: Phone={phone_number}, Message={reply_message_1}")
                continue  

            # ✅ Prepare data for Airtable update
            save_data = {
                "fields": {
                    "email": email,
                    "name": name,  
                    "whatsapp_sentiment": whatsapp_sentiment,
                    "phone_number": phone_number if phone_number else "N/A",
                    "reply_message_1": reply_message_1,
                    "reply_message_2": reply_message_2,
                    "profile_picture_url": profile_picture_url,
                    "whatsapp_reply_time": reply_time,
                    "whatsapp_sent_time": created_time
                }
            }

            # ✅ Send data to dashboard_inbox
            save_response = requests.post(DASHBOARD_INBOX_URL, json=save_data, headers=HEADERS)
            if save_response.status_code == 200:
                saved_count += 1
                logging.info(f"✅ Successfully saved: {save_data}")
            else:
                logging.error(f"❌ Failed to save: {save_response.text}")

        return jsonify({"message": f"Processed and saved {saved_count} records successfully"}), 200

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Airtable API error: {e}")
        return jsonify({"error": str(e)}), 500
