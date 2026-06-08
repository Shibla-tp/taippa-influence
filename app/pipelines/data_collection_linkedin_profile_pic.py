import os
import tempfile
import traceback
import requests
import pickle
import time

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from airtable import Airtable
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID

# ==============================
# CONFIG
# ==============================

# TABLE_NAME = "influencers_linkedin_v3"
TABLE_NAME = "influencers_instagram_registered"
airtable = Airtable(AIRTABLE_BASE_ID, TABLE_NAME, AIRTABLE_API_KEY)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, 'credentials.json')
TOKEN_PATH = os.path.join(PROJECT_ROOT, 'token.pickle')
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# ==============================
# GOOGLE DRIVE AUTH
# ==============================

def get_authenticated_drive_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)

# ==============================
# UPLOAD TO DRIVE
# ==============================

def upload_file_to_drive(file_path, filename):
    drive_service = get_authenticated_drive_service()

    file_metadata = {"name": filename}
    media = MediaFileUpload(file_path, mimetype="image/jpeg")

    uploaded = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    file_id = uploaded.get("id")

    # Make public
    drive_service.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"}
    ).execute()

    return f"https://drive.google.com/uc?id={file_id}&export=download"

# ==============================
# DOWNLOAD + UPLOAD
# ==============================

def process_and_upload_image(profile_pic_url):
    try:
        response = requests.get(profile_pic_url, stream=True, timeout=20)

        if response.status_code != 200:
            return None

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            for chunk in response.iter_content(1024):
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name

        filename = os.path.basename(tmp_file_path)
        drive_url = upload_file_to_drive(tmp_file_path, filename)

        os.remove(tmp_file_path)

        return drive_url

    except Exception:
        traceback.print_exc()
        return None

# ==============================
# MAIN PROCESS FUNCTION
# ==============================

def process_all_profile_pics():

    try:
        # Fetch only records without attachment
        records = airtable.get_all(
            formula="AND({instagram_profile_pic} != '', NOT({saved_profile_pic}))"
        )

        processed = 0
        failed = 0

        for record in records:
            record_id = record["id"]
            fields = record.get("fields", {})
            profile_pic_url = fields.get("instagram_profile_pic")

            if not profile_pic_url:
                continue

            print(f"Processing: {profile_pic_url}")

            drive_url = process_and_upload_image(profile_pic_url)

            if drive_url:
                airtable.update(record_id, {
                    "downloadable_profile_pic": drive_url,  # Text field
                    "saved_profile_pic": [                  # Attachment field
                        {
                            "url": drive_url
                        }
                    ]
                })

                processed += 1
                print("Saved as attachment successfully")

            else:
                failed += 1
                print("Failed to process image")

            time.sleep(0.3)  # avoid rate limits

        return {
            "status": "completed",
            "processed": processed,
            "failed": failed
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e)
        }
