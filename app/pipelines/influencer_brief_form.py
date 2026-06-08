import os
import pickle
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pyairtable import Api
# from config import AIRTABLE_API_KEY,AIRTABLE_BASE_ID


AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"SCRIPT_DIR: {SCRIPT_DIR}")
PICKLE_DIR = os.path.join(SCRIPT_DIR, 'config')

CREDENTIALS_PATH = os.path.join(PICKLE_DIR, "credentials.json")  
print(f"CREDENTIALS_PATH: {CREDENTIALS_PATH}")
TOKEN_PATH = os.path.join(PICKLE_DIR, "token.pickle")
UPLOAD_DIR = "uploads"
SCOPES = ['https://www.googleapis.com/auth/drive.file']


print(f"AIRTABLE_API_KEY: {AIRTABLE_API_KEY}")
print(f"AIRTABLE_BASE_ID: {AIRTABLE_BASE_ID}")

def unique_key_check_airtable(column_name,unique_value,table_name):
        try:
            api = Api(AIRTABLE_API_KEY)
            airtable_obj = api.table(AIRTABLE_BASE_ID, table_name)
            records = airtable_obj.all()
            # print(f"\nCompleted unique key check")
            return any(record['fields'].get(column_name) == unique_value for record in records) 
        except Exception as e:
            print(f"Error occured in {__name__} while performing unique value check in airtable. {e}") 

# function to export data to Airtable
def export_to_airtable(data,raw_table):
    try:
        # print(f"\nExporting results to Airtable")
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, raw_table)
        response = airtable_obj.create(data)
        if 'id' in response:
            print("Record inserted successfully:", response['id'])
        else:
            print("Error inserting record:", response)
    except Exception as e:
        print(f"Error occured in {__name__} while exporting the data to Airtable. {e}")


# Authenticate Drive
def get_authenticated_drive_service():
    creds = None
    # Load existing token
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    # Refresh or request new credentials if not valid
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

# Upload file to Drive
def upload_to_drive(local_path, file_name):
    drive_service = get_authenticated_drive_service()
    file_metadata = {"name": file_name}
    media = MediaFileUpload(local_path)
    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()
    file_id = uploaded_file.get("id")

    # Make file public
    drive_service.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"}
    ).execute()

    drive_url = f"https://drive.google.com/uc?id={file_id}&export=download"
    return drive_url,file_id,drive_service

# Streamlit UI
st.title('📂 Brand Influencer Brief')
st.write('Upload Word, Excel, or PDF file')

brand_id = st.text_input('Brand ID', placeholder='e.g. rayban')
uploaded_file = st.file_uploader(
    "Upload file (Excel, Word, or PDF):",
    type=['xlsx', 'xls', 'doc', 'docx', 'pdf']
)

if uploaded_file and brand_id:
    # Save file locally
    folder_path = os.path.join(UPLOAD_DIR, brand_id)
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"✅ Saved file to: {file_path}")

    # Upload to Drive
    drive_url,file_id,drive_service = upload_to_drive(file_path, uploaded_file.name)
    st.success(f"✅ Uploaded to Drive: {drive_url}")
    # 2. Make file public
    drive_service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
    ).execute()

    # 3. Generate direct download URL
    drive_urls = [f"https://drive.google.com/uc?id={file_id}&export=download"]
    print(f"Drive URL: {drive_urls}")
    record_id = f"{brand_id}_{uploaded_file.name}"
    brand_details = {
        "record_id": str(record_id),
        "brand_id": str(brand_id),
        "file_url": str(drive_urls)
    }
    record_exists = unique_key_check_airtable('instagram_url',brand_details["record_id"],"brand_influencer_brief_docs")
    if not record_exists:
        print(f"Record doesn't exist")
        export_to_airtable(brand_details,"brand_influencer_brief_docs")
    else:
        print(f"Record Exists")

elif uploaded_file and not brand_id:
    st.warning("Please enter a Brand ID before uploading a file.")