import os
import openai
import json
from db.db_ops import db_manager
from config import OPENAI_API_KEY
from flask import Flask, request

app = Flask(__name__)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def extract_appointment_details(email_text):
    system_prompt = (
        "You are an AI that extracts structured event information from raw email text. "
        "Respond ONLY in valid JSON format with the following fields:\n"
        '{\n'
        '  "Event_type": "",\n'
        '  "Invitee": "",\n'
        '  "Invitee_email": "",\n'
        '  "Event_date": "",\n'
        '  "Event_time": "",\n'
        '  "Timezone": "",\n'
        '  "Location": ""\n'
        '}\n'
        "Do not include any explanation or extra text. Output only valid JSON."
    )

    user_prompt = f"Email content:\n{email_text}\n\nExtract the information as specified."

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    raw_output = response.choices[0].message.content.strip()
    print("🔍 Raw OpenAI response:", raw_output)

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        raise ValueError("OpenAI returned invalid JSON.")

def booking_meeting_tracker(data):
    try:
        # raw_text = data["Text_Content"]
        # if not raw_text:
        #     raise ValueError("Text_Content is empty or missing.")

        # result = extract_appointment_details(raw_text)
        # print("✅ Extracted Result:", result)

        # Basic validation
        # if not result.get("Invitee_email"):
        #     raise ValueError("Missing 'Invitee_email' in extracted data.")

        inbox_record = {
            "email": data["email"],
            "full_name": data["full_name"],
            "booking_date_time": data['booking_date_time'],
            "event_type": data["event_type"],
            "phone_number": data["phone"]
        }

        db_manager.insert_data("booking_records", inbox_record)
        print("📥 Data inserted into DB successfully.")

    except Exception as e:
        print(f"❌ Error during booking tracker: {e}")
        raise


