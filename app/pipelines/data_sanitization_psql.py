from flask import Flask, jsonify, request
import pandas as pd
import numpy as np
import re
import psycopg2
from db.db_utils import retrieve_client_tables, phone_number_updation
from datetime import datetime

# Flask app setup
app = Flask(__name__)
from db.db_ops import db_manager
# db = DatabaseManager(
#     ssh_username='magmostafa',
#     ssh_password='Drowssap_2024',
#     postgres_hostname="magmostafa-4523.postgres.pythonanywhere-services.com",
#     postgres_host_port=14523, 
#     db_user='super',
#     db_password='drowsapp_2025',
#     db_name='taippa'
#     )

# # PostgreSQL connection
# conn = psycopg2.connect(
#     dbname="taippa",
#     user="super",
#     password="drowsapp_2025",
#     host="magmostafa-4523.postgres.pythonanywhere-services.com",
#     port="14523"
# )
# cursor = conn.cursor()

def clean_urls(url, unique_id, column_name):
    if pd.isna(url) or not str(url).strip() or url.lower() in ["unknown", "n/a"]:
        placeholder_url = f"https://Unknown-{column_name}-{unique_id}.com"
        print(f"Missing {column_name} for ID {unique_id}, using placeholder: {placeholder_url}")
        return placeholder_url
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url

# def fetch_client_details_postgres(df, icp_field="associated_client_id", client_details_field="client_id"):
#     try:
#         client_ids = df[icp_field].dropna().unique().tolist()
#         if not client_ids:
#             return pd.DataFrame()
#         format_strings = ','.join(['%s'] * len(client_ids))
#         query = f"SELECT * FROM client_info WHERE {client_details_field} IN ({format_strings})"
#         cursor.execute(query, tuple(client_ids))
#         rows = cursor.fetchall()
#         colnames = [desc[0] for desc in cursor.description]
#         return pd.DataFrame([dict(zip(colnames, row)) for row in rows])
#     except Exception as e:
#         print(f"Error fetching client details from PostgreSQL: {e}")
#         return pd.DataFrame()  

# def record_exists(unique_id, table_name):
#     try:
#         query = f"SELECT 1 FROM {table_name} WHERE unique_id = %s LIMIT 1"
#         cursor.execute(query, (unique_id,))
#         exists = cursor.fetchone() is not None
#         print(f"Checking existence for {unique_id} in {table_name}: {exists}")
#         return exists
#     except Exception as e:
#         print(f"Error in record_exists: {e}")
#         return False

# def insert_record(row_dict, table_name):
#     try:
#         columns = ', '.join(row_dict.keys())
#         values = ', '.join(['%s'] * len(row_dict))
#         query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
#         print(f"\n--- INSERTING INTO {table_name} ---")
#         print(f"Query: {query}")
#         print(f"Values: {tuple(row_dict.values())}")
#         cursor.execute(query, tuple(row_dict.values()))
#         conn.commit()
#         print(f"✅ Inserted record into {table_name}")
#     except Exception as e:
#         print(f"❌ Insert error into {table_name}: {e}")
#         print(f"Data: {row_dict}")
#         conn.rollback()

def send_to_postgres_if_new(df, table_name, unique_field, desired_fields=None, field_mapping=None, default_values=None, icp_to_outreach=None, icp_df=None):
    for i, row in df.iterrows():
        try:
            record_data = row.dropna().to_dict()
            print(f"\n🔁 Processing row {i}...")

            if desired_fields:
                record_data = {field: record_data[field] for field in desired_fields if field in record_data}
                print(f"Filtered to desired fields: {list(record_data.keys())}")

            # Build unique_id
            unique_id_value = f"{record_data.get('apollo_id', '')}_{record_data.get('email', '')}"
            record_data["unique_id"] = unique_id_value

            # Apply ICP enrichment
            if icp_to_outreach and icp_df is not None:
                client_id = row.get("associated_client_id")
                if client_id:
                    matching_icp_rows = icp_df[icp_df["client_id"] == client_id]
                    if not matching_icp_rows.empty:
                        for outreach_field, icp_field in icp_to_outreach.items():
                            if icp_field in matching_icp_rows.columns:
                                record_data[outreach_field] = matching_icp_rows.iloc[0][icp_field]

            # Map field names
            if field_mapping:
                record_data = {field_mapping.get(k, k): v for k, v in record_data.items()}
                print(f"After field mapping: {list(record_data.keys())}")

            # Add created_time
            record_data["created_time"] = datetime.now()
            
            # Apply default values
            if default_values:
                for key, value in default_values.items():
                    record_data.setdefault(key, value)
            print(f"📦 Final record_data before insert: {record_data}")
            # Insert if not exists
            print(f"Unique Field:{unique_field}")
            if not db_manager.unique_key_check(unique_field, unique_id_value, table_name):
                db_manager.insert_data(table_name, record_data)
            else:
                print(f"⚠️ Record {i} already exists in {table_name}, skipping.")
        except Exception as e:
            print(f"❌ Error processing record {i}: {e}")

def sanitize_data(client_id, data_dict):
    try:
        raw_table_name, cleaned_table_name, outreach_table_name = retrieve_client_tables(client_id)
        print(f"\n📥 Tables: raw={raw_table_name}, cleaned={cleaned_table_name}, outreach={outreach_table_name}")

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

        df = df.drop_duplicates(subset=['apollo_id', 'email'])
        df = df[~((df['email'].str.lower() == "unknown") | (df['linkedin_url'].str.lower() == "unknown"))]
        filtered_df = df.copy()

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
        

        client_ids = df["associated_client_id"].dropna().unique().tolist()
        print(f"Client ids:{client_ids}")
        # icp_df = db_manager.fetch_client_details(client_ids)
        icp_df_dict = db_manager.get_record("client_info","client_id",client_ids[0])
        # print(f"Client ids:{client_ids}")
        icp_df = pd.DataFrame([icp_df_dict])
        # icp_df = fetch_client_details_postgres(df)
        # icp_df = dbget_record(self,table_name,primary_key_col,primary_key_value):
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
        # Save to cleaned table
        send_to_postgres_if_new(df, cleaned_table_name, unique_field='unique_id')
        send_to_postgres_if_new(
            filtered_df,
            outreach_table_name,
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
            icp_df=icp_df,
            default_values={"status": "inactive"}
        )

        return {"message": "Data cleaned and processed successfully."}

    except Exception as e:
        print(f"❌ Error in sanitize_data: {e}")
        return {"error": f"Error in sanitizing data: {e}"}


