import io
import pickle
import requests
from flask import Flask, request, jsonify
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

app = Flask(__name__)

# === Config ===
AIRTABLE_API_KEY = 'patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3'
BASE_ID = 'app5s8zl7DsUaDmtx'
TABLE_NAME = 'brand_influencer_brief_docs'
FIELD_NAME = 'images'

TOKEN_PICKLE = 'token.pickle'  # path to your saved pickle token
PRESENTATION_ID = '1-oS2h8REmpApMWvf0MT63LevqhK5QFjKqRTpaeKsHE8'

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/presentations']

def get_credentials():
    creds = None
    with open(TOKEN_PICKLE, 'rb') as token:
        creds = pickle.load(token)
    # If expired, refresh token
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PICKLE, 'wb') as token:
            pickle.dump(creds, token)
    return creds

def insert_image_from_airtable(record_id):
    creds = get_credentials()
    drive_service = build('drive', 'v3', credentials=creds)
    slides_service = build('slides', 'v1', credentials=creds)

    # 1. Fetch image URL from Airtable record
    airtable_url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}/{record_id}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    res = requests.get(airtable_url, headers=headers)
    res.raise_for_status()
    record = res.json()

    if FIELD_NAME not in record['fields'] or len(record['fields'][FIELD_NAME]) == 0:
        return {"status": "error", "message": f"No images found in field '{FIELD_NAME}'"}

    image_url = record['fields'][FIELD_NAME][0]['url']

    # 2. Download image
    image_content = requests.get(image_url).content

    # 3. Upload image to Google Drive
    media = MediaIoBaseUpload(io.BytesIO(image_content), mimetype='image/jpeg')
    file_metadata = {'name': f"{record_id}.jpg"}
    drive_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = drive_file.get('id')

    # 4. Make the file publicly accessible
    permission = {'type': 'anyone', 'role': 'reader'}
    drive_service.permissions().create(fileId=file_id, body=permission).execute()

    # 5. Insert image into Google Slides (first slide)
    presentation = slides_service.presentations().get(presentationId=PRESENTATION_ID).execute()
    slide_id = presentation['slides'][0]['objectId']

    requests_body = {
        "requests": [{
            "createImage": {
                "url": f"https://drive.google.com/uc?id={file_id}",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "height": {"magnitude": 300, "unit": "PT"},
                        "width": {"magnitude": 300, "unit": "PT"}
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": 100,
                        "translateY": 100,
                        "unit": "PT"
                    }
                }
            }
        }]
    }
    slides_service.presentations().batchUpdate(presentationId=PRESENTATION_ID, body=requests_body).execute()

    return {
        "status": "success",
        "file_id": file_id,
        "drive_link": f"https://drive.google.com/uc?id={file_id}",
        "message": "Image inserted into Google Slides."
    }




if __name__ == '__main__':
    app.run(debug=True)
