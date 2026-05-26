import requests
from urllib.parse import urlencode
from db.db_utils import retrieve_record
from db.db_ops import db_manager
from config import INSTANTLY_API_KEY,LEADSIN_API_KEY

def add_lead_leadsin(apollo_id,campaign_id,outreach_table_name):
    try:
        primary_key_col = "apollo_id"
        primary_key_value = apollo_id
        record = retrieve_record(outreach_table_name,primary_key_col,primary_key_value)
        # record = db_manager.get_record(outreach_table_name,primary_key_col,primary_key_value)
        print(f"----Record retrieved:---- {record}")
        # profileUrl = record.get('fields').get("linkedin_profile_url","Not available")
        # email = record.get('fields').get("recipient_email","Not available")
        # first_name = record.get('fields').get("recipient_first_name","Not available")
        # last_name = record.get('fields').get("recipient_last_name","Not available")
        # message1 = record.get('fields').get("linkedin_message","Not available")
        # message2 = record.get('fields').get("linkedin_message_2","Not available")
        # subject1 = record.get('fields').get("linkedin_subject","Not available")
        # connection_message = record.get('fields').get("linkedin_connection_message","Not available")

        profileUrl = record.get('fields').get("linkedin_profile_url","Not available")
        email = record.get('fields').get("recipient_email","Not available")
        first_name = record.get('fields').get("recipient_first_name","Not available")
        last_name = record.get('fields').get("recipient_last_name","Not available")
        message1 = record.get('fields').get("linkedin_message","Not available")
        message2 = record.get('fields').get("linkedin_message_2","Not available")
        message3 = record.get('fields').get("linkedin_message_3","Not available")
        message4 = record.get('fields').get("linkedin_message_4","Not available")
        message5 = record.get('fields').get("linkedin_message_5","Not available")
        subject1 = record.get('fields').get("linkedin_subject","Not available")
        subject2 = record.get('fields').get("linkedin_subject_2","Not available")
        subject3 = record.get('fields').get("linkedin_subject_3","Not available")
        subject4 = record.get('fields').get("linkedin_subject_4","Not available")
        subject5 = record.get('fields').get("linkedin_subject_5","Not available")

        # profileUrl = record.get("linkedin_profile_url","Not available")
        # email = record.get("recipient_email","Not available")
        # first_name = record.get("recipient_first_name","Not available")
        # last_name = record.get("recipient_last_name","Not available")
        # message1 = record.get("linkedin_message","Not available")
        # message2 = record.get("linkedin_message_2","Not available")
        # message3 = record.get("linkedin_message_3","Not available")
        # message4 = record.get("linkedin_message_4","Not available")
        # message5 = record.get("linkedin_message_5","Not available")
        # subject1 = record.get("linkedin_subject","Not available")
        # subject2 = record.get("linkedin_subject_2","Not available")
        # subject3 = record.get("linkedin_subject_3","Not available")
        # subject4 = record.get("linkedin_subject_4","Not available")
        # subject5 = record.get("linkedin_subject_5","Not available")

        connection_message = record.get("linkedin_connection_message","Not available")

        print(f"Profile URL: {profileUrl}")
        print(f"Email: {email}")
        print(f"First Name: {first_name}")
        print(f"Last Name: {last_name}")
        print(f"Connection Message: {connection_message}")
        print(f"Message 1: {message1}")
        print(f"Message 2: {message2}")
        print(f"Message 3: {message3}")
        print(f"Message 4: {message4}")
        print(f"Message 5: {message5}")
        print(f"Subject 1: {subject1}")
        print(f"Subject 2: {subject2}")
        print(f"Subject 3: {subject3}")
        print(f"Subject 4: {subject4}")
        print(f"Subject 5: {subject5}")

        profile_details = {
        "apollo_id":apollo_id,
        "profileUrl": profileUrl,
        "email":email,
        "first_name": first_name,
        "last_name": last_name,
        "connection_message": connection_message,
        "message1": message1,
        "message2": message2,
        "message3": message3,
        "message4": message4,
        "message5": message5,
        "subject1": subject1,
        "subject2": subject2,
        "subject3": subject3,
        "subject4": subject4,
        "subject5": subject5,
        "removeDbDuplicates":"true",
        }
        
        url = f"https://api.multilead.io/api/open-api/v1/campaign/{campaign_id}/leads"

        headers = {
            'Authorization': LEADSIN_API_KEY,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(url, headers=headers, data=urlencode(profile_details))
        print(response.text)
        print("Successfully added the lead to the campaign")
        return True
    except Exception as e:
        print(f"Error occured while retrieving leads from the outreach table. Error: {e}")
        return False

def add_lead_instantly(payload):
  try:
    url = "https://api.instantly.ai/api/v2/leads"
    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {INSTANTLY_API_KEY}"
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    print(data)
  except Exception as e:
    print(f"Error occured while adding leads to the campaign in Instantly.ai for the lead: {payload}. Error: {e}")


# def add_lead_leadsin_campaign(campaign_id,payload):
#   try:
#     url = f"https://api.multilead.io/api/open-api/v1/campaign/{campaign_id}/leads"

#     headers = {
#         'Authorization': LEADSIN_API_KEY,
#         'Content-Type': 'application/x-www-form-urlencoded'
#     }

#     response = requests.post(url, headers=headers, data=urlencode(payload))
#     print(response.text)
    
#   except Exception as e:
#     print(f"Error occured while adding leads to the campaign for the lead: {payload} . Error: {e}")