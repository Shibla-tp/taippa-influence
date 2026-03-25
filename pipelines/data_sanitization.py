from flask import Flask, jsonify, request 
from airtable import Airtable
import pandas as pd
import numpy as np
import os
import re
import json
from db.db_utils import retrieve_client_tables,phone_number_updation
from datetime import datetime

app = Flask(__name__)

# Old Airtable Configuration
BASE_ID_OLD = 'app5s8zl7DsUaDmtx'
API_KEY = 'patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3'  # Replace with a secure method to fetch the key
TABLE_NAME_OLD = 'profiles_raw'

# New Airtable Configuration
BASE_ID_NEW = 'app5s8zl7DsUaDmtx'
TABLE_NAME_NEW = 'profiles_cleaned'
TABLE_NAME_NEW1 = 'profiles_outreach'
# TABLE_NAME_NEW2 = 'client_details'
TABLE_NAME_NEW2 = os.getenv("CLIENT_INFO_TABLE_NAME")
print(f"Client table name for Santization module : {TABLE_NAME_NEW2}")
TABLE_NAME_NEW3 = 'contacts_taippa_marketing'
TABLE_NAME_EMAIL_OPENED = 'email_opened'
TABLE_NAME_LINK_CLICKED = 'link_opened'
TABLE_NAME_METRICS = 'metrics'
TABLE_NAME_EMAIL_SENT = 'email_sent'
TABLE_NAME_REPLIES_RECIEVED = 'replies_received'
TABLE_NAME_LEAD_MAGNET = 'lead_magnet_details'
API_KEY_NEW = os.getenv('AIRTABLE_API_KEY', 'patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3')

airtable_old = Airtable(BASE_ID_OLD, TABLE_NAME_OLD, API_KEY)
airtable_new = Airtable(BASE_ID_NEW, TABLE_NAME_NEW, API_KEY_NEW)
airtable_new1 = Airtable(BASE_ID_NEW, TABLE_NAME_NEW1, API_KEY_NEW)
airtable_new3 = Airtable(BASE_ID_NEW, TABLE_NAME_NEW3, API_KEY_NEW)
airtable_email = Airtable(BASE_ID_NEW, TABLE_NAME_EMAIL_OPENED, API_KEY_NEW)
airtable_link = Airtable(BASE_ID_NEW, TABLE_NAME_LINK_CLICKED, API_KEY_NEW)
airtable_email_sent = Airtable(BASE_ID_NEW, TABLE_NAME_EMAIL_SENT, API_KEY_NEW)
airtable_replies_received = Airtable(BASE_ID_NEW, TABLE_NAME_REPLIES_RECIEVED, API_KEY_NEW)
airtable_metrics = Airtable(BASE_ID_NEW, TABLE_NAME_METRICS, API_KEY_NEW)
airtable_lead_magnet = Airtable(BASE_ID_NEW, TABLE_NAME_LEAD_MAGNET, API_KEY_NEW)
try:
    airtable_new2 = Airtable(BASE_ID_NEW, TABLE_NAME_NEW2, API_KEY_NEW)
except Exception as e:
    print(f"Error initializing Airtable: {e}")

from datetime import datetime


def send_to_airtable_if_new(df, airtable_instance, unique_field, desired_fields=None, field_mapping=None, default_values=None, icp_to_outreach=None, icp_df=None):
    for i, row in df.iterrows():
        try:
            record_data = row.dropna().to_dict()

            if desired_fields:
                record_data = {field: record_data[field] for field in desired_fields if field in record_data}

            unique_id_value = f"{record_data.get('apollo_id', '')}_{record_data.get('email', '')}"
            record_data["unique_id"] = unique_id_value

            if icp_to_outreach and icp_df is not None:
                client_id = row.get("associated_client_id")
                if client_id:
                    matching_icp_rows = icp_df[icp_df["client_id"] == client_id]
                    if not matching_icp_rows.empty:
                        for outreach_field, icp_field in icp_to_outreach.items():
                            if icp_field in matching_icp_rows.columns:
                                record_data[outreach_field] = matching_icp_rows.iloc[0][icp_field]

            if field_mapping:
                record_data = {field_mapping.get(k, k): v for k, v in record_data.items()}

            record_data["created_time"] = str(datetime.now())

            if default_values:
                for key, value in default_values.items():
                    record_data.setdefault(key, value)

            search_result = airtable_instance.search(unique_field, unique_id_value)
            if not search_result:
                airtable_instance.insert(record_data)
                print(f"Record {i} inserted successfully into {airtable_instance}.")
            else:
                print(f"Record {i} already exists in {airtable_instance}. Skipping insertion.")

        except Exception as e:
            print(f"Error processing record {i}: {e}")

def fetch_client_details(df, airtable_instance, icp_field="associated_client_id", client_details_field="client_id"):
    client_details = []
    for _, row in df.iterrows():
        client_id = row.get(icp_field)
        if client_id:
            records = airtable_instance.search(client_details_field, client_id)
            if records:
                client_details.append(records[0]['fields'])
    return pd.DataFrame(client_details)

def clean_urls(url, unique_id, column_name):
    if pd.isna(url) or not str(url).strip() or url.lower() in ["unknown", "n/a"]:
        placeholder_url = f"https://Unknown-{column_name}-{unique_id}.com"
        print(f"Missing {column_name} for ID {unique_id}, using placeholder: {placeholder_url}")
        return placeholder_url
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url

def sanitize_data(client_id, data_dict):
    try:
        raw_table_name, cleaned_table_name, outreach_table_name = retrieve_client_tables(client_id)

        cleaned_table = Airtable(BASE_ID_NEW, cleaned_table_name, API_KEY_NEW)
        outreach_table = Airtable(BASE_ID_NEW, outreach_table_name, API_KEY_NEW)

        df = pd.DataFrame([data_dict])
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.where(pd.notnull(df), None)

        for column in df.select_dtypes(include=['object']).columns:
            df[column] = df[column].fillna("Unknown")

        if 'first_name' in df.columns:
            df['first_name'] = df['first_name'].str.strip().str.capitalize()
        if 'last_name' in df.columns:
            df['last_name'] = df['last_name'].str.strip().str.capitalize()

        if 'email' in df.columns:
            df['email'] = (
                df['email']
                .astype(str)
                .str.lower()
                .str.strip()
                .apply(lambda x: re.sub(r'\+.*?@', '@', x))
            )
            
        df['unique_id'] = df['apollo_id'].fillna("Unknown") + "_" + df['email'].fillna("Unknown")
        if 'linkedin_url' in df.columns:
            df['linkedin_url'] = df.apply(
                lambda row: clean_urls(row['linkedin_url'], row['unique_id'], 'linkedin_url'),
                axis=1
            )

        

        
        # df['created_time'] = str(datetime.now())
        df = df.drop_duplicates(subset=['apollo_id', 'email'])
        df = df[~((df['email'].str.lower() == "unknown") | (df['linkedin_url'].str.lower() == "unknown"))]
        filtered_df = df[~((df['email'].str.lower() == "unknown") | (df['linkedin_url'].str.lower() == "unknown"))]
        



        campaign_field_mapping = {
            "first_name": "recipient_first_name",
            "last_name": "recipient_last_name",
            "email": "recipient_email",
            "organization_name": "recipient_company",
            "title": "recipient_role",
            "organization_website": "recipient_company_website",
            "organization_short_description": "recipient_bio",
            "linkedin_url": "linkedin_profile_url",
            
        }

        icp_df = fetch_client_details(df, airtable_new2, icp_field="associated_client_id", client_details_field="client_id")

        icp_to_outreach_mapping = {
            "sender_email": "email",
            "sender_company": "company_name",
            "sender_name": "full_name",
            "sender_title": "job_title",
            "sender_company_website": "company_website",
            "client_value_proposition": "client_value_proposition",
            "cta_options": "cta_options",
            "color_scheme": "color_scheme",
            "font_style": "font_style",
            "instantly_campaign_id": "instantly_campaign_id",
            "business_type": "business_type",
            "outreach_table": "outreach_table"
        }

        # Send to cleaned Airtable
        send_to_airtable_if_new(df, cleaned_table, unique_field='unique_id')

        # Send to outreach Airtable
        send_to_airtable_if_new(
            filtered_df,
            outreach_table,
            unique_field="unique_id",
            desired_fields=[
                "linkedin_url",
                "first_name",
                "last_name",
                "email",
                "organization_name",
                "title",
                "organization_website",
                "organization_short_description",
                "unique_id",
                "apollo_id",
                "associated_client_id",
                "employment_summary",
                "created_time", 
                "filter_criteria",
                "target_region"
            ],
            field_mapping=campaign_field_mapping,
            icp_to_outreach=icp_to_outreach_mapping,
            icp_df=icp_df
        )

        return {"message": "Data cleaned and processed successfully."}

    except Exception as e:
        return {"error": f"Error in sanitizing data: {e}"}

@app.route('/test_sanitize', methods=['POST'])
def test_sanitize():
    try:
        data = request.get_json()
        client_id = data.get("client_id")
        data_dict = data.get("data_dict")
        if not client_id or not data_dict:
            return jsonify({"error": "Missing 'client_id' or 'data_dict' in request body"}), 400
        
        result = sanitize_data(client_id, data_dict)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
@app.route('/update-email-opens', methods=['POST'])
def update_email_opens():
    try:
        # Step 1: Fetch all records from email_opened table
        email_records = airtable_email.get_all()
        email_df = pd.DataFrame([record['fields'] for record in email_records])

        # Step 2: Count the number of emails opened for each campaign_id
        if 'campaign_id' not in email_df.columns:
            return jsonify({"error": "campaign_id column is missing in email_opened table"}), 400

        email_count = email_df['campaign_id'].value_counts().to_dict()

        # Step 3: Fetch all records from airtable_link table to count all emails clicked per campaign_id
        link_records = airtable_link.get_all()
        link_df = pd.DataFrame([record['fields'] for record in link_records])

        # Step 4: Count the total number of emails clicked for each campaign_id (not unique)
        if 'campaign_id' not in link_df.columns or 'email' not in link_df.columns:
            return jsonify({"error": "campaign_id or email column is missing in airtable_link table"}), 400

        # Count all occurrences of email for each campaign_id (instead of unique emails)
        email_click_count = link_df.groupby('campaign_id')['email'].count().to_dict()

        # Step 5: Fetch all records from airtable_email_sent table for unique email count
        email_sent_records = airtable_email_sent.get_all()
        email_sent_df = pd.DataFrame([record['fields'] for record in email_sent_records])

        # Ensure required columns exist
        if 'campaign_id' not in email_sent_df.columns or 'email' not in email_sent_df.columns:
            return jsonify({"error": "campaign_id or email column is missing in airtable_email_sent table"}), 400

        # Count unique emails for each campaign_id
        unique_email_count = email_sent_df.groupby('campaign_id')['email'].nunique().to_dict()
        # Step 6: Fetch all records from airtable_email_sent table for unique email count
        email_reply_records = airtable_replies_received.get_all()
        email_reply_df = pd.DataFrame([record['fields'] for record in email_reply_records])

        # Ensure required columns exist
        if 'campaign_id' not in email_reply_df.columns or 'email' not in email_reply_df.columns:
            return jsonify({"error": "campaign_id or email column is missing in airtable_email_sent table"}), 400

        # Count unique emails for each campaign_id
        reply_count = email_reply_df.groupby('campaign_id')['email'].nunique().to_dict()

        # Step 7: Update the metrics table with opened, clicked, and unique email counts
        for campaign_id in set(email_count.keys()).union(email_click_count.keys()).union(unique_email_count.keys()):
            # Search for the record in the metrics table
            metrics_record = airtable_metrics.search('campaign_id', campaign_id)
            if metrics_record:
                record_id = metrics_record[0]['id']
                update_data = {}

                # Update the opened count
                if campaign_id in email_count:
                    update_data["opened"] = str(email_count[campaign_id])  # Convert to string for long text

                # Update the clicked count
                if campaign_id in email_click_count:
                    update_data["clicked"] = str(email_click_count[campaign_id])  # Convert to string for long text

                # Update the unique email count
                if campaign_id in unique_email_count:
                    update_data["sequence_started"] = str(unique_email_count[campaign_id])  # Convert to string for long text

                # Update the unique email count
                if campaign_id in reply_count:
                    update_data["replies_received"] = str(reply_count[campaign_id])  # Convert to string for long text

                # Update the record in Airtable
                airtable_metrics.update(record_id, update_data)
                print(f"Updated campaign_id {campaign_id} with data: {update_data}")

        return jsonify({"message": "Opened, clicked, and unique email counts updated successfully in metrics table"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def sanitize_data(client_id, data_dict):
    try:
        raw_table_name, cleaned_table_name, outreach_table_name = retrieve_client_tables(client_id)

        cleaned_table = Airtable(BASE_ID_NEW, cleaned_table_name, API_KEY_NEW)
        outreach_table = Airtable(BASE_ID_NEW, outreach_table_name, API_KEY_NEW)

        df = pd.DataFrame([data_dict])
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.where(pd.notnull(df), None)

        for column in df.select_dtypes(include=['object']).columns:
            df[column] = df[column].fillna("Unknown")

        if 'first_name' in df.columns:
            df['first_name'] = df['first_name'].str.strip().str.capitalize()
        if 'last_name' in df.columns:
            df['last_name'] = df['last_name'].str.strip().str.capitalize()

        if 'email' in df.columns:
            df['email'] = (
                df['email']
                .astype(str)
                .str.lower()
                .str.strip()
                .apply(lambda x: re.sub(r'\+.*?@', '@', x))
            )
            
        df['unique_id'] = df['apollo_id'].fillna("Unknown") + "_" + df['email'].fillna("Unknown")
        if 'linkedin_url' in df.columns:
            df['linkedin_url'] = df.apply(
                lambda row: clean_urls(row['linkedin_url'], row['unique_id'], 'linkedin_url'),
                axis=1
            )

        

        
        # df['created_time'] = str(datetime.now())
        df = df.drop_duplicates(subset=['apollo_id', 'email'])
        df = df[~((df['email'].str.lower() == "unknown") | (df['linkedin_url'].str.lower() == "unknown"))]
        filtered_df = df[~((df['email'].str.lower() == "unknown") | (df['linkedin_url'].str.lower() == "unknown"))]
        



        campaign_field_mapping = {
            "first_name": "recipient_first_name",
            "last_name": "recipient_last_name",
            "email": "recipient_email",
            "organization_name": "recipient_company",
            "title": "recipient_role",
            "organization_website": "recipient_company_website",
            "organization_short_description": "recipient_bio",
            "linkedin_url": "linkedin_profile_url",
            
        }

        icp_df = fetch_client_details(df, airtable_new2, icp_field="associated_client_id", client_details_field="client_id")

        icp_to_outreach_mapping = {
            "sender_email": "email",
            "sender_company": "company_name",
            "sender_name": "full_name",
            "sender_title": "job_title",
            "sender_company_website": "company_website",
            "client_value_proposition": "client_value_proposition",
            "cta_options": "cta_options",
            "color_scheme": "color_scheme",
            "font_style": "font_style",
            "instantly_campaign_id": "instantly_campaign_id",
            "business_type": "business_type",
            "outreach_table": "outreach_table"
        }

        # Send to cleaned Airtable
        send_to_airtable_if_new(df, cleaned_table, unique_field='unique_id')

        # Send to outreach Airtable
        send_to_airtable_if_new(
            filtered_df,
            outreach_table,
            unique_field="unique_id",
            desired_fields=[
                "linkedin_url",
                "first_name",
                "last_name",
                "email",
                "organization_name",
                "title",
                "organization_website",
                "organization_short_description",
                "unique_id",
                "apollo_id",
                "associated_client_id",
                "employment_summary",
                "created_time", 
                "filter_criteria",
                "target_region"
            ],
            field_mapping=campaign_field_mapping,
            icp_to_outreach=icp_to_outreach_mapping,
            icp_df=icp_df
        )

        return {"message": "Data cleaned and processed successfully."}

    except Exception as e:
        return {"error": f"Error in sanitizing data: {e}"}

@app.route('/fetch_and_update_data', methods=['POST'])
def fetch_and_update_data():
    try:
        data = request.get_json()
        client_id = data.get("client_id")
        data_dict = data.get("data_dict")
        if not client_id or not data_dict:
            return jsonify({"error": "Missing 'client_id' or 'data_dict' in request body"}), 400
        
        result = sanitize_data(client_id, data_dict)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
from flask import Flask, jsonify, request
import pandas as pd

# Initialize Flask app
app = Flask(__name__)

def fetch_airtable_data(airtable_instance):
    """
    Fetch all records from Airtable and convert them into a cleaned pandas DataFrame.
    """
    records = airtable_instance.get_all()
    data = [record.get('fields', {}) for record in records]
    df = pd.DataFrame(data)
    return clean_dataframe(df)

def clean_dataframe(df):
    """
    Clean the DataFrame by replacing NaN, infinite, and out-of-range float values.
    """
    return df.replace([pd.NA, float('inf'), float('-inf')], None)

def match_and_return_records(lead_magnet_df, new3_df):
    """
    Compare the recipient_email from new3_df with the email from lead_magnet_df.
    Return matched records with apollo_id, recipient_role, and email.
    """
    matched_records = []
    for _, new3_row in new3_df.iterrows():
        recipient_email = new3_row.get('recipient_email')
        matching_row = lead_magnet_df[lead_magnet_df['email'] == recipient_email]
        if not matching_row.empty:
            # Append matched records
            matched_records.append({
                'apollo_id': new3_row.get('apollo_id'),
                'recipient_role': new3_row.get('recipient_role'),
                'email': recipient_email
            })

    # Filter duplicates by email, keeping the most complete record
    unique_records = filter_unique_records(matched_records)
    return unique_records

def filter_unique_records(records):
    """
    Filter duplicate records by email, prioritizing those with valid 'apollo_id' and 'recipient_role'.
    """
    grouped = {}
    for record in records:
        email = record.get('email')
        if not email:
            continue

        if email not in grouped:
            grouped[email] = record
        else:
            # Prioritize the record with valid fields
            if not grouped[email].get('apollo_id') and record.get('apollo_id'):
                grouped[email]['apollo_id'] = record['apollo_id']
            if not grouped[email].get('recipient_role') and record.get('recipient_role'):
                grouped[email]['recipient_role'] = record['recipient_role']

    return list(grouped.values())

def send_to_airtable(airtable_instance, records):
    """
    Update records in the Airtable instance for the corresponding email.
    """
    for record in records:
        email = record.get('email')
        if not email:
            continue

        # Find the Airtable record matching the email
        existing_records = airtable_instance.get_all(formula=f"{{email}} = '{email}'")
        if not existing_records:
            print(f"No record found for email: {email}")
            continue

        # Get the record ID of the first match
        record_id = existing_records[0]['apollo_id']

        # Update the corresponding record with the new data
        update_data = {key: value for key, value in record.items() if key != 'email'}
        airtable_instance.update(record_id, update_data)




@app.route('/fetch-inbox-details', methods=['POST'])
def fetch_inbox_details():
    try:
        # Define the Airtables to update
        tables_to_update = {
            "email_opened": airtable_email,
            "email_sent": airtable_email_sent,
            "replies_received": airtable_replies_received,
            "link_opened": airtable_link
        }

        # Fetch client_details
        client_details_records = airtable_new2.get_all()
        client_details_df = pd.DataFrame([record['fields'] for record in client_details_records])
        print(client_details_df)
        if client_details_df.empty or 'instantly_campaign_id' not in client_details_df.columns or 'cleaned_table' not in client_details_df.columns:
            return jsonify({"error": "No valid instantly_campaign_id or cleaned_table found in client_details"}), 400

        # Create a mapping of campaign_id to cleaned_table
        campaign_to_cleaned_table = dict(zip(
            client_details_df['instantly_campaign_id'], 
            client_details_df['cleaned_table']
        ))

        # Process each table
        for table_name, airtable_instance in tables_to_update.items():
            # Fetch records from the current table
            table_records = airtable_instance.get_all()
            table_df = pd.DataFrame([record['fields'] for record in table_records])

            if table_df.empty or 'email' not in table_df.columns or 'campaign_id' not in table_df.columns:
                continue

            # Iterate through the records
            for _, table_row in table_df.iterrows():
                email = table_row['email']
                campaign_id = table_row['campaign_id']

                # Get the corresponding cleaned_table for the campaign_id
                cleaned_table_name = campaign_to_cleaned_table.get(campaign_id)
                if not cleaned_table_name:
                    continue

                # Access the corresponding cleaned_table
                cleaned_table = Airtable(BASE_ID_NEW, cleaned_table_name, API_KEY_NEW)

                # Fetch the record for the given email directly from cleaned_table
                cleaned_records = cleaned_table.search('email', email)
                if not cleaned_records:
                    continue

                # Extract the name and title fields from the first matching record
                cleaned_record = cleaned_records[0]['fields']
                name = cleaned_record.get('name')
                job_title = cleaned_record.get('title')
                organization_name = cleaned_record.get('organization_name')
                photo_url= cleaned_record.get('photo_url')
                print(cleaned_record)
                # Update the current table with Name and job_title
                airtable_instance.update_by_field(
                    'email',  # Field to match
                    email,  # Field value
                    {"Name": name, "job_title": job_title, "organization_name":organization_name, "profile_picture_url":photo_url}
                )

        return jsonify({"message": "Name and job_title successfully saved in all specified tables"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/post-data', methods=['GET'])
def post_data():
    return {"message": "Data received successfully"}, 200

if __name__ == "__main__":
    # testing
    client_id = "plot_taippa"
    status = fetch_and_update_data(client_id)
    print(status)
    # app.run(debug=True)


