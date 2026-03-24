from flask import Flask, request, jsonify
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

app = Flask(__name__)

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

def process_and_upload_image_with_airtable(profile_pic_url):
    try:
        response = requests.get(profile_pic_url, stream=True)
        if response.status_code != 200:
            return None, "Image download failed"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            for chunk in response.iter_content(1024):
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        filename = os.path.basename(tmp_file_path)
        drive_url = upload_file_to_drive(tmp_file_path, filename)
        os.remove(tmp_file_path)
        return drive_url, None
    except Exception as e:
        traceback.print_exc()
        return None, str(e)

