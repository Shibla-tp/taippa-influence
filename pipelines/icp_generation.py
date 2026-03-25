import openai
import ast
import os
import json
import requests
from error_logger import execute_error_block
from db.db_utils import unique_key_check_airtable,export_to_airtable,update_client_info,fetch_client_column,retrieve_column_value,update_column_value
from pipelines.lead_website_analysis import web_analysis
from config import APOLLO_HEADERS
from db.db_ops import db_manager

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLIENT_CONFIG_TABLE_NAME = os.getenv("CLIENT_CONFIG_TABLE_NAME")
CLIENT_DETAILS_TABLE_NAME = os.getenv("CLIENT_DETAILS_TABLE_NAME")
CLIENT_INFO_TABLE_NAME = os.getenv("CLIENT_INFO_TABLE_NAME")

def construct_query_param_range(key, values):
    print("&".join([f"{key}[]={value.replace(',', '%2C')}" for value in values]))
    return "&".join([f"{key}[]={value.replace(',', '%2C')}" for value in values])

def construct_query_param_keywords(key, value):
    return f"{key}={value.replace(',', '%2C').replace(' ','%20')}"

def construct_query_param(key, values):
    res = "&".join([f"{key}[]={value.replace(' ', '%20').replace(',', '%2C')}" for value in values])
    print(res)
    return "&".join([f"{key}[]={value.replace(' ', '%20').replace(',', '%2C')}" for value in values])

def lowercase_keys(json_data, keys_to_lowercase):
    for key in keys_to_lowercase:
        if key in json_data and isinstance(json_data[key], list):
            json_data[key] = [value.lower() for value in json_data[key] if isinstance(value, str)]
    return json_data

def generate_apollo_url(client_id,page_number=1,records_required=2,organization=""):
    try:
        config_details = db_manager.get_record(CLIENT_CONFIG_TABLE_NAME,"client_id",client_id)
        icp_job_details = ast.literal_eval(config_details.get("icp_job_details"))
        icp_job_seniorities = ast.literal_eval(config_details.get("icp_job_seniorities"))
        icp_employee_range = ast.literal_eval(config_details.get("icp_employee_range"))
        icp_locations = ast.literal_eval(config_details.get("icp_locations"))
        organization_domains = ast.literal_eval(config_details.get("organization_domains"))
        organization_last_index= int(config_details.get("organization_last_index"))
        # icp_job_details = ast.literal_eval(fetch_client_column("client_config",client_id,"icp_job_details"))
        # icp_job_seniorities = ast.literal_eval(fetch_client_column("client_config",client_id,"icp_job_seniorities"))
        # icp_employee_range = ast.literal_eval(fetch_client_column("client_config",client_id,"icp_employee_range"))
        # icp_locations = ast.literal_eval(fetch_client_column("client_config",client_id,"icp_locations"))
        # organization_domains = ast.literal_eval(fetch_client_column("client_config",client_id,"organization_domains"))
        # organization_last_index= int(fetch_client_column("client_config",client_id,"organization_last_index"))
        email_status = ['verified']
        organization_domains_new = organization_domains[organization_last_index:organization_last_index+2]
        print(f"================== ICP Generation for client id: {client_id}==================")
        print(f"Organization last index: {organization_last_index}")
        print(f"Organization domains: {organization_domains_new}")
        print(f"=====================================================================")
        if organization_last_index >= len(organization_domains):
            print(f"\n\n =========================== All the domains have been processed. Resetting the organization last index =========================== ")
            organization_last_index = 0
            organization_domains_new = organization_domains[organization_last_index:organization_last_index+2]
            db_manager.update_single_field(table_name=CLIENT_CONFIG_TABLE_NAME,column_name= "organization_last_index", column_value=organization_last_index, primary_key_col="client_id", primary_key_value=client_id)
            # update_column_value(
            #             table_name=CLIENT_CONFIG_TABLE_NAME,
            #             column_name="organization_last_index",
            #             column_value=organization_last_index,
            #             primary_key_col="client_id",
            #             primary_key_value=client_id)
        print('Creating query params')
        query_params = [
                    construct_query_param("person_titles", icp_job_details),
                    construct_query_param("person_seniorities", icp_job_seniorities),
                    # construct_query_param("person_locations", icp_employee_range),
                    # construct_query_param("organization_num_employees_ranges", icp_employee_range),
                    construct_query_param("organization_locations", icp_locations),
                    construct_query_param("contact_email_status", email_status),
                    construct_query_param("q_organization_domains_list", organization_domains_new),
                    construct_query_param_range("organization_num_employees_ranges", icp_employee_range),
        ]
        
        query_params_test = query_params.copy()
        query_params.append(f"include_similar_titles=true")
        query_params.append(f"page={page_number}")
        query_params_test.append(f"page=1")
        query_params.append(f"per_page={records_required}")
        query_params_test.append(f"per_page=100")
        base_url = "https://api.apollo.io/api/v1/mixed_people/search"
        url_test = f"{base_url}?{'&'.join(query_params_test)}"
        dynamic_url = f"{base_url}?{'&'.join(query_params)}"
        headers = APOLLO_HEADERS    
        # print(f"Running the people search API test")
        # print(f"Apollo Url for testing : {url_test}")
        return dynamic_url
    except Exception as e:
        execute_error_block(f"Error occured while generating the apollo url: {e}")

def generate_icp(client_id,website_url):
    try:
        print(f"\n\n--------Generating ICP --------\n\n")
        openai.api_key = OPENAI_API_KEY
        config_type = retrieve_column_value(CLIENT_INFO_TABLE_NAME,"client_id",client_id,"config_type")
        vector_index_name,icp_apollo_tags = web_analysis(website_url,config_type,client_id)
        print(f"\n\n----ICP Apollo Tags retrieved: {icp_apollo_tags}------\n\n")
        keys_to_lowercase = ["job_titles", "person_seniorities", "person_locations"]
        icp_json = lowercase_keys(icp_apollo_tags, keys_to_lowercase)
        print(f"Updated json: {icp_json}")
        print(f"Completed creating ICP json")
        person_titles = icp_json.get('job_titles') 
        person_seniorities = icp_json.get('person_seniorities')
        person_locations = icp_json.get('person_locations')
        organization_domains=""
        organization_num_employees_ranges = icp_json.get('employee_range')
        print(f"Config table name: {CLIENT_CONFIG_TABLE_NAME}")
        record_exists = unique_key_check_airtable('client_id',client_id,CLIENT_CONFIG_TABLE_NAME)
        if record_exists:
            print(f'Record with the following id: {client_id} already exists for client config table. Skipping the entry...')
            return True
        
        config_data = {
            "client_id":client_id,
            "icp_job_details":str(person_titles),
            "icp_job_seniorities":str(person_seniorities),
            "icp_employee_range":str(organization_num_employees_ranges),
            "icp_locations":str(person_locations),
            "page_number":'1',
            "qualify_leads":'yes',
            "refresh_type":'custom',
            "records_required":'10',
            "organization_domains":str(organization_domains),
            "include_organization":'yes' if str(config_type).upper() == 'CUSTOM' else 'no',
            "organization_last_index":'0',
            "icp_flag":'no' if str(config_type).upper() == 'CUSTOM' else 'yes',
            "is_active":"yes",
            "vector_index_name":vector_index_name,
        }
        export_to_airtable(config_data, CLIENT_CONFIG_TABLE_NAME)
        return icp_json
    
    except Exception as e:
        execute_error_block(f"Error occured at {__name__} while generating icp: {e}")

if __name__=="__main__":
    pass