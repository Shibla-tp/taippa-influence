import requests
import json
from error_logger import execute_error_block

# Replace with your Airtable Base ID and Personal Access Token (PAT)
API_KEY = "pataU3bOHPNEqpE9J.01f448eb1dadb92df25ec47c8f4483e29f7be7307cd6d2172cf11f7b7120de00"
BASE_ID = "app5s8zl7DsUaDmtx"

# URL for retrieving all tables in the base
url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def generate_table(phase,table_name,description):
    try:
        if table_exists(table_name):
          print(f"Table '{table_name}' already exists.")
          return
        else:
          print(f"Table '{table_name}' does not exist. Creating it...")
        url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"
        if phase != 'outreach':
            schema = {
                "name": table_name,
                "description": description,
                "fields": [
                    {
                        "name": "id",
                        "type": "multilineText"
                    },
                    {
                        "name": "first_name",
                        "type": "multilineText"
                    },
                    {
                        "name": "last_name",
                        "type": "multilineText"
                    },
                    {
                        "name": "name",
                        "type": "multilineText"
                    },
                    {
                        "name": "email",
                        "type": "multilineText"
                    },
                    {
                        "name": "phone",
                        "type": "multilineText"
                    },
                    {
                        "name": "linkedin_url",
                        "type": "multilineText"
                    },
                    {
                        "name": "title",
                        "type": "multilineText"
                    },
                    {
                        "name": "seniority",
                        "type": "multilineText"
                    },
                    {
                        "name": "headline",
                        "type": "multilineText"
                    },
                    {
                        "name": "is_likely_to_engage",
                        "type": "multilineText"
                    },
                    {
                        "name": "photo_url",
                        "type": "multilineText"
                    },
                    {
                        "name": "email_status",
                        "type": "multilineText"
                    },
                    {
                        "name": "twitter_url",
                        "type": "multilineText"
                    },
                    {
                        "name": "github_url",
                        "type": "multilineText"
                    },
                    {
                        "name": "facebook_url",
                        "type": "multilineText"
                    },
                    {
                        "name": "organization_name",
                        "type": "multilineText"
                    },
                    {
                        "name": "organization_website",
                        "type": "multilineText"
                    },
                    {
                        "name": "organization_linkedin",
                        "type": "multilineText"
                    },
                    {
                        "name": "organization_facebook",
                        "type": "multilineText"
                    },
                    {
                        "name": "organization_primary_phone",
                        "type": "multilineText"
                    },
                    {
                        "name": "organization_logo",
                        "type": "multilineText"
                    },
                    {
                        "name": "organization_primary_domain",
                        "type": "multilineText"
                    },
                    {
                        "name": "organization_industry",
                        "type": "multilineText"
                    },
                    {
                        "name": "organization_estimated_num_employees",
                        "type": "multilineText"
                    },
                    {
                        "name": "organization_phone",
                        "type": "multilineText"
                    },
                    {
                        "name": "organization_city",
                        "type": "multilineText"
                    },
                    {
                        "name": "organization_state",
                        "type": "multilineText"
                    },
                    {
                        "name": "organization_country",
                        "type": "multilineText"
                    },
                    {
                        "name": "organization_short_description",
                        "type": "multilineText"
                    },
                    {
                        "name": "employment_history",
                        "type": "multilineText"
                    },
                    {
                        "name": "organization_technology_names",
                        "type": "multilineText"
                    },
                    {
                        "name": "employment_summary",
                        "type": "multilineText"
                    },
                    {
                        "name": "associated_client_id",
                        "type": "multilineText"
                    },
                    {
                        "name": "unique_id",
                        "type": "multilineText"
                    },
                    {
                        "name": "created_time",
                        "type": "multilineText"
                    },
                ]
            }
        else:
            schema = {
            "name": table_name,
            "description": description,
            "fields": [
                {
                    "name": "id",
                    "type": "multilineText"
                },
                {
                    "name": "recipient_first_name",
                    "type": "multilineText"
                },
                {
                    "name": "recipient_last_name",
                    "type": "multilineText"
                },
                {
                    "name": "recipient_role",
                    "type": "multilineText"
                },
                {
                    "name": "recipient_company",
                    "type": "multilineText"
                },
                {
                    "name": "recipient_company_website",
                    "type": "multilineText"
                },
                {
                    "name": "recipient_bio",
                    "type": "multilineText"
                },
                {
                    "name": "recipient_phone",
                    "type": "multilineText"
                },
                {
                    "name": "recipient_email",
                    "type": "multilineText"
                },
                {
                    "name": "sender_name",
                    "type": "multilineText"
                },
                {
                    "name": "sender_title",
                    "type": "multilineText"
                },
                {
                    "name": "sender_company",
                    "type": "multilineText"
                },
                {
                    "name": "sender_email",
                    "type": "multilineText"
                },
                {
                    "name": "sender_company_website",
                    "type": "multilineText"
                },
                {
                    "name": "cta_options",
                    "type": "multilineText"
                },
                {
                    "name": "color_scheme",
                    "type": "multilineText"
                },
                {
                    "name": "font_style",
                    "type": "multilineText"
                },
                {
                    "name": "subject",
                    "type": "multilineText"
                },
                {
                    "name": "email",
                    "type": "multilineText"
                },
                {
                    "name": "follow_up",
                    "type": "multilineText"
                },
                {
                    "name": "linkedin_profile_url",
                    "type": "multilineText"
                },
                {
                    "name": "unique_id",
                    "type": "multilineText"
                },
                {
                    "name": "associated_client_id",
                    "type": "multilineText"
                },
                {
                    "name": "employment_summary",
                    "type": "multilineText"
                },
                {
                    "name": "instantly_campaign_id",
                    "type": "multilineText"
                },
                {
                    "name": "business_type",
                    "type": "multilineText"
                },
                {
                    "name": "outreach_table",
                    "type": "multilineText"
                },
                {
                    "name": "client_value_proposition",
                    "type": "multilineText"
                },
                {
                    "name": "processed",
                    "type": "multilineText"
                },
                {
                    "name": "processed_date",
                    "type": "multilineText"
                },
                {
                    "name": "instantly_status",
                    "type": "multilineText"
                },
                {
                    "name": "enriched_data",
                    "type": "multilineText"
                },
                {
                    "name": "created_time",
                    "type": "multilineText"
                },
            ]
            }
        response = requests.post(url, headers=headers, data=json.dumps(schema)) 
        if response.status_code == 200:
            print(f"Table `{table_name}` created successfully for {phase} layer")
            # print(response.json())
        else:
            execute_error_block(f"Failed to create table: {response.text}")
            raise 
    
    except Exception as e:
        execute_error_block(f"Error occured while generating table for {phase} layer. {e}")
        # raise 

def table_exists(table_name):
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        tables = response.json().get("tables", [])
        for table in tables:
            if table["name"] == table_name:
                return True
        return False
    else:
        execute_error_block(f"Failed to fetch tables: {response.status_code} - {response.text}")
        # return False

def create_client_tables(client_id):
  try:
    print(f"Creating client tables for {client_id}")
    src_table = "src_" + client_id
    cur_table = "cur_" + client_id
    outreach_table = "outreach_" + client_id
    generate_table("collection",src_table,f"Source Table for {client_id}")
    generate_table("curation",cur_table,f"Cleaned Table for {client_id}")
    generate_table("outreach",outreach_table,f"Outreach Table for {client_id}")
    print(f"Successfully created tables for {client_id}")
    return src_table, cur_table, outreach_table
  except Exception as e:
    execute_error_block(f"Exception occured while creating table: {e}")
  
if __name__ == "__main__":
    try:
        create_client_tables("testing")
    except Exception as e:
        execute_error_block(f"Exception occured while creating table :{e}")