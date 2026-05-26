import os
import tempfile
import pickle
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from flask import jsonify
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PICKLE_DIR = os.path.join(SCRIPT_DIR, 'files')
SCOPES = ['https://www.googleapis.com/auth/drive.file']

TOKEN_PATH = os.path.join(PICKLE_DIR, 'token.pickle')
AIRTABLE_TABLE_NAME = "brand_influencer_brief_docs"
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

def get_authenticated_drive_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("Token missing or invalid. Please upload a valid token.pickle.")
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

def upload_file_to_drive(file_obj, drive_service):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        file_obj.save(tmp.name)
        file_metadata = {"name": file_obj.filename}
        media = MediaFileUpload(tmp.name, resumable=True)
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

    file_id = uploaded_file.get("id")

    drive_service.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()

    return f"https://drive.google.com/uc?id={file_id}&export=download"

def handle_upload_and_submit_to_airtable(brand_id, files):
    drive_service = get_authenticated_drive_service()
    file_urls = [upload_file_to_drive(f, drive_service) for f in files]

    file_urls_str = "[" + ",".join(f'"{url}"' for url in file_urls) + "]"


    payload = {
        "fields": {
            "brand_id": brand_id,
            "documents": [{"url": url} for url in file_urls],  # for attachments field
            "file_url": file_urls_str  # for long text field
        }
    }
def handle_upload_and_submit_to_airtable(brand_id, files, images):
    drive_service = get_authenticated_drive_service()

    # Upload documents
    document_urls = [upload_file_to_drive(f, drive_service) for f in files]
    # Upload images
    image_urls = [upload_file_to_drive(img, drive_service) for img in images]

    # Prepare Airtable payload
    payload = {
        "fields": {
            "brand_id": brand_id,
            "documents": [{"url": url} for url in document_urls],  # Attachment field
            "images": [{"url": url} for url in image_urls],        # New attachment field for images
            "file_url": "[" + ",".join(f'"{url}"' for url in document_urls) + "]",
            "image_url": "[" + ",".join(f'"{url}"' for url in image_urls) + "]"  # Optional: store as text
        }
    }

    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(AIRTABLE_URL, headers=headers, json=payload)
    if response.status_code not in (200, 201):
        return jsonify({"status": "failed", "airtable_error": response.text}), 400

    return jsonify({
        "status": "success",
        "uploaded_files": file_urls,
        "uploaded_documents": document_urls,
        "uploaded_images": image_urls,
        "airtable_response": response.json()
    }), 201
