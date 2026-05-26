import os
import time
from datetime import datetime
import datetime as dt
from pyairtable import Table,Api
import openai
import requests
from error_logger import execute_error_block
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS,PERPLEXITY_API_KEY

# Config tables required
CLIENT_DETAILS_TABLE_NAME = os.getenv("CLIENT_DETAILS_TABLE_NAME")
CLIENT_CONFIG_TABLE_NAME = os.getenv("CLIENT_CONFIG_TABLE_NAME")
CLIENT_INFO_TABLE_NAME = os.getenv("CLIENT_INFO_TABLE_NAME")

def update_column_value(table_name,column_name,column_value,primary_key_col,primary_key_value):
    try:
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, table_name)
        data_records = airtable_obj.all(formula=f"{{{primary_key_col}}} = '{primary_key_value}'")
        if data_records:
            record = data_records[0] 
            record_id = record.get('id')
            airtable_obj.update(record_id, {column_name: str(column_value)})
        else:
            print(f"No record found for {primary_key_col} '{primary_key_value}'")
    except Exception as e:
      execute_error_block(f"Error occured in {__name__} while updating the column in airtable. {e}")


def update_record(table_name,record,primary_key_col):
    try:
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, table_name)
        record_id = record[primary_key_col]
        data_records = airtable_obj.all(formula=f"{{{primary_key_col}}} = '{record_id}'")
        if data_records:
            record_to_update = data_records[0] 
            record_id_to_update = record_to_update.get('id')            
            airtable_obj.update(record_id_to_update, record)
            return True
        else:
            print(f"No record found for record_id {record_id}")
            return False
            
    except Exception as e:
      execute_error_block(f"Error occured in {__name__} while updating the record in airtable. {e}")

def retrieve_record(table_name,primary_key_col,primary_key_value):
    try:
        api = Api(AIRTABLE_API_KEY) 
        airtable_obj = api.table(AIRTABLE_BASE_ID, table_name)
        record_details = airtable_obj.all(formula=f"{{{primary_key_col}}} = '{primary_key_value}'")
        records_count = len(record_details)
        if records_count <1:
            execute_error_block(f"No records found for the corresponding {primary_key_col} {primary_key_value} in {table_name}")
        record = record_details[0]
        return record
        
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while fetching record from table {table_name}. {e}")

def retrieve_column_value(table_name,primary_key_col,primary_key_value,column_name):
    try:
        print(f'Fetching {column_name} for {primary_key_col} -> {primary_key_value}')
        api = Api(AIRTABLE_API_KEY) 
        airtable_obj = api.table(AIRTABLE_BASE_ID, table_name)
        record_details = airtable_obj.all(formula=f"{{{primary_key_col}}} = '{primary_key_value}'")
        # print(f"Matching record count present in {table_name} for column_name {column_name} : {len(record_details)}")
        records_count = len(record_details)
        if records_count <1:
            execute_error_block(f"No records found for the corresponding {primary_key_col} {primary_key_value} in {table_name}")
        record_details = record_details[0]
        column_value = record_details.get('fields').get(column_name,"Not available")
        print(column_value)
        return column_value
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while fetching client specific column details. {e}")

def get_source_data(table_name):
    try:
        airtable = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, table_name)
        # Fetch all records from src_guideline table
        records = airtable.all()
        # Convert records to list of dictionaries
        guidelines_list = [{"id": rec["id"], **rec["fields"]} for rec in records]
        print(f"Total records fetched from the source table {table_name}: {len(guidelines_list)}")
        return guidelines_list

    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while fetching source data from airtable. {e}")


def retrieve_client_tables(client_id):
    try:
        # print('Retreiving tables')
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, CLIENT_INFO_TABLE_NAME)
        records = airtable_obj.all()
        records_list = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")
        if len(records_list) < 1:
            execute_error_block(f"The following client_id `{client_id}` is not present in the table {CLIENT_INFO_TABLE_NAME}")
        record_details = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")[0]
        raw_table = record_details.get('fields').get('raw_table')
        cleaned_table = record_details.get('fields').get('cleaned_table')
        outreach_table = record_details.get('fields').get('outreach_table')
        return raw_table,cleaned_table,outreach_table
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while retrieving tables from airtable. {e}")

def fetch_client_outreach_mappings(client_id):
    try:
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, CLIENT_INFO_TABLE_NAME)
        record = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")[0].get('fields')
        return {
            "email": record.get("email"),
            "company_name": record.get("company_name"),
            "full_name": record.get("full_name"),
            "job_title": record.get("job_title"),
            "company_website": record.get("company_website"),
            "solution_benefits": record.get("solution_benefits"),
            "solution_impact_examples": record.get("solution_impact_examples"),
            "unique_features": record.get("unique_features"),
            "cta_options": record.get("cta_options"),
            "color_scheme": record.get("color_scheme"),
            "font_style": record.get("font_style"),
            "instantly_campaign_id": record.get("instantly_campaign_id"),
            "business_type": record.get("business_type"),
            "outreach_table": record.get("outreach_table")
        }
    
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while fetching client mappings. {e}")

def fetch_latest_created_time(table_name):
    try:
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, table_name)
        latest_record = airtable_obj.all(sort=["-created_time"], max_records=1)
        if len(latest_record) <1:
            latest_created_time = datetime.now()
        else:
            latest_created_time = latest_record[0]['fields']['created_time']
        return latest_created_time
    except Exception as e:
        execute_error_block(f"Error occurred while fetching latest created time: {e}")


def fetch_record_count_after_time(table_name, latest_created_time):
    try:
        # Parse the string to datetime object
        
        latest_created_time = datetime.strptime(latest_created_time, "%Y-%m-%d %H:%M:%S.%f")
        
        # Round down to the nearest minute
        latest_created_time = latest_created_time.replace(second=0, microsecond=0)
        
        # Initialize Airtable API
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, table_name)

        # Format the datetime object to ISO 8601
        formatted_time = latest_created_time.isoformat()

        # Use a filter formula to get records created on or after `latest_created_time`
        filter_formula = f"IS_AFTER(CREATED_TIME(), '{formatted_time}')"
        
        # Fetch all matching records
        records = airtable_obj.all(formula=filter_formula)

        # Filter records manually to get more precise results
        filtered_records = [record for record in records if datetime.fromisoformat(record['createdTime']) > latest_created_time]

        # Count the number of records
        record_count = len(filtered_records)

        print(f"Total records added after {latest_created_time}: {record_count}")
        return record_count
    
    except Exception as e:
        execute_error_block(f"Error occurred while fetching record count: {e}")


def fetch_client_details(client_id):
    try:
        # print(f"\nFetching Client Details")
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, CLIENT_INFO_TABLE_NAME)
        record = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")[0]
        solution_benefits = record['fields']['solution_benefits']
        unique_features = record['fields']['unique_features']
        solution_impact_examples = record['fields']['solution_impact_examples']
        domain = record['fields']['domain']
        buyer_criteria = record['fields']['buyer_criteria']
        buyer_examples = record['fields']['buyer_examples']
        # print(f"\nSuccessfully fetched client details")
        return solution_benefits,unique_features,solution_impact_examples,domain,buyer_criteria,buyer_examples
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while fetching client details. {e}")

def get_clients_config(client_config_table):
    try:
        # print('Fetching clients list from config table')
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, client_config_table)
        config_data = airtable_obj.all()
        # print('Successfully fetched clients list from config table')
        return config_data
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while fetching client config details. {e}")

def update_client_config(client_config_table,client_id,profiles_enriched):
    try:
        # print('Updating data sync status')
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, client_config_table)
        # print(f"Client id = '{client_id}'")
        data_records = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")
        if data_records:
            record = data_records[0] 
            record_id = record.get('id')
            page_number = int(record.get('fields').get('page_number', 0))
            new_page_number = page_number
            # new_page_number = page_number + 1
            airtable_obj.update(record_id, {'page_number': str(new_page_number),'records_fetched':str(profiles_enriched)})
            # print(f"Updated page_number to {new_page_number} for client_id {client_id}")
        else:
            print(f"No record found for client_id {client_id}")

    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while updating latest page number. {e}")

def fetch_page_config(client_config_table,client_id):
    try:
        # print('Fetching latest page number')
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, client_config_table)
        # print(f"\n Fetching latest page configuration from the table for the client: {client_id}")
        data_count = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")
        record_details = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")[0]
        page_number = record_details.get('fields').get('page_number')
        records_required = record_details.get('fields').get('records_required')
        active_status = record_details.get('fields').get('is_active')
        # print(f"Successfully fetched latest page configuration from the client config table for the client: {client_id}")
        return page_number,records_required,active_status
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while fetching latest page number. {e}")

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
        execute_error_block(f"Error occured in {__name__} while exporting the data to Airtable. {e}")


def unique_key_check_airtable(column_name,unique_value,table_name):
    try:
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, table_name)
        records = airtable_obj.all()
        # print(f"\nCompleted unique key check")
        return any(record['fields'].get(column_name) == unique_value for record in records) 
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while performing unique value check in airtable. {e}")

def parse_people_info(data):
    try:
        # print('----------Parsing the data input --------------]')
        employment_history = data['employment_history']

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
          model="gpt-4",
          messages=[{"role": "system", "content": "You are an expert at text summarization."},
          {"role": "user", "content": f"Please summarize this description: {employment_history}"}
          ],
        )
        employment_summary = response.choices[0].message.content
        parsed_people_info={
            "title":data.get('title'),
            "headline":data.get('headline'),
            "country":data.get('country'),
            "city":data.get('city'),
            "departments":data.get('departments'),
            "subdepartments":data.get('subdepartments'),
            "functions":data.get('functions'),
            "employment_summary":employment_summary
        }
        return parsed_people_info
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while parsing the data input. {e}")

def update_client_info(client_info_table,client_id,company_value_proposition):
    try:
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, client_info_table)
        # print(f"\nFetching latest page number from the table")
        data_records = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")
        if data_records:
            record = data_records[0] 
            record_id = record.get('id')
            airtable_obj.update(record_id, {'client_value_proposition': str(company_value_proposition)})
        else:
            print(f"No record found for client_id {client_id}")
    except Exception as e:
        execute_error_block(f"Exception occured in {__name__} while updating company value proposition. {e}")

def update_client_vector(client_config_table,client_id,index_name):
    try:
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, client_config_table)
        data_records = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")
        if data_records:
            record = data_records[0] 
            record_id = record.get('id')
            airtable_obj.update(record_id, {'vector_index_name': index_name})
        else:
            print(f"No record found for client_id {client_id}")
    except Exception as e:
        execute_error_block(f"Exception occured in {__name__} while updating vector index name. {e}")


def add_apollo_webhook_info(data,apollo_table):
    try:
        # print(f"\nExporting results to Airtable")
        # print(f"Request data for airtable: {data}")
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, apollo_table)
        response = airtable_obj.create(data)
        if 'id' in response:
            print("Record inserted successfully for the apollo webhook:", response['id'])
        else:
            print("Error inserting record for the apollo webhook:", response)
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while adding apollo webhook details. {e}")


def fetch_client_column(client_info_table,client_id,column_name):
    try:
        # print(f'Fetching {column_name} for client {client_id}')
        api = Api(AIRTABLE_API_KEY) 
        airtable_obj = api.table(AIRTABLE_BASE_ID, client_info_table)
        record_details = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")
        # print(record_details)
        # print(f"Matching record count present in the client config table for column_name {column_name} : {len(record_details)}")
        records_count = len(record_details)
        if records_count <1:
            execute_error_block(f"No records found for the corresponding client_id {client_id} in the {client_info_table} table")
        record_details = record_details[0]
        column_value = record_details.get('fields').get(column_name,"Not available")
        # print(column_value)
        return column_value
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while fetching client specific column details. {e}")

def add_client_tables_info(client_id,source_table_name,curated_table_name,outreach_table_name):
    try:
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, CLIENT_INFO_TABLE_NAME)
        data_records = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")
        retries = 7
        while retries!= 0:
            # print(f"Checking data count in the client info table for client_id {client_id}...")
            data_records = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")
            if data_records:
                record = data_records[0] 
                record_id = record.get('id')
                airtable_obj.update(record_id, {'raw_table': str(source_table_name),'cleaned_table':str(curated_table_name),'outreach_table':str(outreach_table_name)})
                print(f"Added client info table with the dependent tables")
                return
            else:
                print(f"Retrying the table check... Retries left : {retries}")
                time.sleep(10)
                retries -= 1
        execute_error_block(f"No record found for client_id {client_id} in client_info table for updating dependent tables info")
    except Exception as e:
        execute_error_block(f"Error occured while adding client tables info: {e}")

def get_apollo_phone_number(apollo_id):
  try:
        print('Fetching Apollo phone number from the webhook response')
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, "apollo_webhook")
        data = record_details = airtable_obj.all(formula=f"{{apollo_id}} = '{apollo_id}'")
        if len(data) > 0:
          record_details = airtable_obj.all(formula=f"{{apollo_id}} = '{apollo_id}'")[0]
          response = record_details.get('fields').get('phone')
          print(f"Successfully fetched phone number from Apollo for the apollo_id: {apollo_id}")
        else:
          return {"status":f"error, no record found for apollo_id {apollo_id}"}
        return response
  except Exception as e:
        execute_error_block(f"Error occured in {__name__} while fetching the apollo phone number. {e}")

def update_phone_numbers(apollo_id,table_name,col_name,col_value):
  try:
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, table_name)
        print(f"Apollo id = '{apollo_id}'")
        data_records = airtable_obj.all(formula=f"{{apollo_id}} = '{apollo_id}'")
        if data_records:
            record = data_records[0] 
            record_id = record.get('id')
            airtable_obj.update(record_id, {col_name:str(col_value)})
            print(f"Updated phone number to {col_value} for apollo_id {apollo_id}")
        else:
            print(f"No record found for apollo_id {apollo_id}")
  except Exception as e:
    execute_error_block(f"Exception occured while updating the phone numbers: {e}")

def phone_number_updation(apollo_id,cur_table_name,outreach_table_name):
  try:
    phone = get_apollo_phone_number(apollo_id)
    cur_col_name = "phone"
    outreach_col_name = "recipient_phone"
    col_value = phone
    update_phone_numbers(apollo_id,cur_table_name,cur_col_name,col_value)
    update_phone_numbers(apollo_id,outreach_table_name,outreach_col_name,col_value)
    print("Successfully updated the phone numbers for the apollo entries")
    return phone
  except Exception as e:
    execute_error_block(f"Error occured while updating phone numbers for Apollo entries")