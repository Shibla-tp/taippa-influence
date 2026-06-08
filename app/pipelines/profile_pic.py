import os
import tempfile
import traceback
import requests
import pickle

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from airtable import Airtable
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID

TABLE_NAME = "influencers_instagram_v3"
airtable = Airtable(AIRTABLE_BASE_ID, TABLE_NAME, AIRTABLE_API_KEY)

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, 'credentials.json')
TOKEN_PATH = os.path.join(PROJECT_ROOT, 'token.pickle')
SCOPES = ['https://www.googleapis.com/auth/drive.file']


def get_authenticated_drive_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)
    return build("drive", "v3", credentials=creds)


def upload_file_to_drive(file_path, filename):
    drive_service = get_authenticated_drive_service()
    file_metadata = {"name": filename}
    media = MediaFileUpload(file_path, mimetype="image/jpeg", resumable=False)
    uploaded = drive_service.files().create(
        body=file_metadata, media_body=media, fields="id"
    ).execute()

    file_id = uploaded.get("id")
    drive_service.permissions().create(
        fileId=file_id, body={"role": "reader", "type": "anyone"}
    ).execute()

    return f"https://drive.google.com/uc?id={file_id}&export=download"


def process_and_upload_image(profile_pic_url, record_id):
    try:
        # Download image
        response = requests.get(profile_pic_url, stream=True)
        if response.status_code != 200:
            return {"status": "failed", "message": "Image download failed"}, 400

        # Save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            for chunk in response.iter_content(1024):
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name

        # Upload to Drive
        filename = os.path.basename(tmp_file_path)
        drive_url = upload_file_to_drive(tmp_file_path, filename)

        # Airtable update
        airtable.update(record_id, {
            "saved_profile_pic": [{"url": drive_url}],
            "downloadable_profile_pic": drive_url
        })

        os.remove(tmp_file_path)

        return {"status": "success", "drive_url": drive_url}, 200

    except Exception as e:
        traceback.print_exc()
        return {"status": "failed", "message": str(e)}, 500
