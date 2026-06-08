import os
import ast
import concurrent.futures

from datetime import datetime
# from pipelines.data_sanitization import fetch_and_update_data
from pipelines.data_sanitization import sanitize_data
from db.db_utils import fetch_client_details,parse_people_info,unique_key_check_airtable,export_to_airtable,retrieve_client_tables,fetch_client_outreach_mappings,get_clients_config,fetch_page_config,update_client_config,phone_number_updation,fetch_client_column,get_source_data,update_column_value,retrieve_record
from error_logger import execute_error_block
from pipelines.data_extractor import people_search_v2,manual_data_insertion
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS
from pipelines.icp_generation import generate_apollo_url
from db.db_ops import db_manager

# from lead_magnet.industry_insights import get_cold_email_kpis

CLIENT_DETAILS_TABLE_NAME = os.getenv("CLIENT_DETAILS_TABLE_NAME")
CLIENT_CONFIG_TABLE_NAME = os.getenv("CLIENT_CONFIG_TABLE_NAME")

def trigger_custom_pipeline(client_id):
    try:
        print(f"\n================= Scheduled Pipeline Execution Started for Client {client_id} ==========================================\n")
        # retrieve_record
        # record = retrieve_record(CLIENT_CONFIG_TABLE_NAME,"client_id",client_id)
        config_details = db_manager.get_record(CLIENT_CONFIG_TABLE_NAME,"client_id",client_id)
        # record_details = record
        if config_details:
            print(f"Client configuration exists for client id : {client_id}")
        else:
            print(f"Client configuration does not exist for client id : {client_id}")
            return
        # print(record_details)
        qualify_leads = config_details.get('qualify_leads')
        print(f"Qualify leads: {qualify_leads}")
        index_name = config_details.get('vector_index_name')
        # index_name = db_manager.get_record(CLIENT_CONFIG_TABLE_NAME,"vector_index_name",client_id)
        # index_name = fetch_client_column(CLIENT_CONFIG_TABLE_NAME,client_id,"vector_index_name")
        print(f"Index name: {index_name}")
        # return
        last_page,records_required,active_status = config_details.get('page_number'),config_details.get('records_required'),config_details.get('is_active')
        # last_page,records_required,active_status = fetch_page_config(CLIENT_CONFIG_TABLE_NAME,client_id)
        if not active_status or active_status.upper() == 'NO':
            print(f"Skipping data sync since the entry is not active")
            print(f"\n-------------------- Data Sync Skipped for Client : {client_id}------------------------\n")
            return
        print(f"Formatting the dynamic url for Apollo search for client {client_id}")
        include_organization = config_details.get('include_organization')
        organization_last_index = config_details.get('organization_last_index')
        # include_organization = fetch_client_column(CLIENT_CONFIG_TABLE_NAME,client_id,"include_organization")
        if include_organization.upper()=="YES":
            # page_numbers = [1,2,3,4,5,6,7,8,9,10,11,12,13]
            page_numbers = [1]
            # organization_last_index= fetch_client_column("client_config",client_id,"organization_last_index")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(process_organization, page_number, client_id, records_required, qualify_leads, index_name,organization_last_index)
                    for page_number in page_numbers
                ]
            concurrent.futures.wait(futures)

            organization_last_index = db_manager.get_column_value(column_name="organization_last_index",table_name=CLIENT_CONFIG_TABLE_NAME,primary_key_col="client_id",primary_key_value=client_id)
            # organization_last_index= fetch_client_column("client_config",client_id,"organization_last_index")
            organization_last_index_updated = str(int(organization_last_index)+2)
            db_manager.update_single_field(table_name=CLIENT_CONFIG_TABLE_NAME,column_name= "organization_last_index", column_value=organization_last_index_updated, primary_key_col="client_id", primary_key_value=client_id)
            # update_column_value(
            #     table_name=CLIENT_CONFIG_TABLE_NAME,
            #     column_name="organization_last_index",
            #     column_value=organization_last_index_updated,
            #     primary_key_col="client_id",
            #     primary_key_value=client_id)
            print(f"Updated the organization last index to {organization_last_index_updated}")
            profiles_enriched = 2
            # print(f"Data Cleaning & Outreach Started")
            # response = fetch_and_update_data(client_id)
            # print(f"Data Cleaning & Outreach Completed")
            print(f"\n------------ Data populated for the outreach table for the client_id: {client_id}\n")
        else:
            print(f"Organization domain flag not set")
        print(f"\n\n======================= Data Sync Completed For Client : {client_id} ======================= \n") 

    except Exception as e:
        execute_error_block(f"Exception occured while triggering the pipeline run {e}")

def process_organization(page_number, client_id, records_required, qualify_leads, index_name,organization_last_index):
    """Function to process each organization"""
    try:
        print(f"\n\n=============== Started Data Ingestion For Page Number: {page_number} ===============\n\n")
        icp_url = generate_apollo_url(client_id, page_number, records_required)
        print(f"Apollo Search Url for the client {client_id}: {icp_url}")
        people_search_v2(icp_url, client_id, qualify_leads, index_name)  # Keeping it as a normal function
        # response = fetch_and_update_data(client_id)
        print(f"\n\n=============== Completed Data Ingestion For Page Number: {page_number} ===============\n\n")

    except Exception as e:
        print(f"Error occurred while running data refresh for the page number: {page_number} - {e}")

# def manual_data_sync(qualify_leads,client_id,index_name):
#     try:
#         records_list = get_source_data("source_table")
#         manual_data_insertion(records_list,qualify_leads,client_id,index_name)
#         response = fetch_and_update_data(client_id)
#         print(f"Completed data cleaning and outreach")
#     except Exception as e:
#         print(f"Error occured while running data sync for client.{e}")

def trigger_pipeline_custom():
    try:
        config_data = get_clients_config(CLIENT_CONFIG_TABLE_NAME)
        print("\n================= Scheduled Pipeline Execution Started ==========================================\n")
        for client_config in config_data:
            try:
                client_details = client_config.get('fields')
                client_id = client_details.get('client_id')
                qualify_leads = client_details.get('qualify_leads')
                index_name = fetch_client_column(CLIENT_CONFIG_TABLE_NAME,client_id,"vector_index_name")
                last_page,records_required,active_status = fetch_page_config(CLIENT_CONFIG_TABLE_NAME,client_id)
                print(f"\n\n======================= Data Sync started for Client : {client_id} ======================= \n") 
                if not active_status or active_status.upper() == 'NO':
                    print(f"Skipping data sync since the entry is not active")
                    print(f"\n-------------------- Data Sync Skipped for Client : {client_id}------------------------\n")
                    continue
                print(f"Formatting the dynamic url for Apollo search for client {client_id}")
                include_organization = fetch_client_column(CLIENT_CONFIG_TABLE_NAME,client_id,"include_organization")
                if include_organization.upper()=="YES":
                    page_numbers = [1,2]
                    organization_last_index= fetch_client_column("client_config",client_id,"organization_last_index")
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = [
                            executor.submit(process_organization, page_number, client_id, records_required, qualify_leads, index_name,organization_last_index)
                            for page_number in page_numbers
                        ]
                        # Wait for all tasks to complete
                    concurrent.futures.wait(futures)
                    organization_last_index= fetch_client_column("client_config",client_id,"organization_last_index")
                    organization_last_index_updated = str(int(organization_last_index)+15)
                    update_column_value(
                        table_name=CLIENT_CONFIG_TABLE_NAME,
                        column_name="organization_last_index",
                        column_value=organization_last_index_updated,
                        primary_key_col="client_id",
                        primary_key_value=client_id)
                    print(f"Updated the organization last index to {organization_last_index_updated}")
                profiles_enriched = 2
                # response = fetch_and_update_data(client_id)
                print(f"Completed data cleaning and outreach")
                # updated_status = update_client_config(CLIENT_CONFIG_TABLE_NAME,client_id,profiles_enriched)
                print(f"\n------------ Data populated for the outreach table for the client_id: {client_id}\n")
                print(f"\n\n======================= Data Sync Completed For Client : {client_id} ======================= \n") 
            except Exception as e:
                print(f"Error occured during data sync for client.{e}")
        
        print("\n================= Scheduled Pipeline Execution Completed ==========================================\n")
        return config_data
    except Exception as e:
        execute_error_block(f"Exception occured while triggering the pipeline run {e}")

def process_client(client_details):
    """Function to process each client"""
    try:
        client_id = client_details.get('client_id')
        organization = ""
        print(f"\n\n=============== Started Data Ingestion For client {client_id} ===============\n\n")
        qualify_leads = client_details.get('qualify_leads')
        last_page,records_required,active_status = fetch_page_config(CLIENT_CONFIG_TABLE_NAME,client_id)
        index_name = fetch_client_column(CLIENT_CONFIG_TABLE_NAME,client_id,"vector_index_name")
        print(f"\n\n======================= Data Sync started for Client : {client_id} ======================= \n") 
        if not active_status or active_status.upper() == 'NO':
            print(f"Skipping data sync since the entry is not active")
            print(f"\n-------------------- Data Sync Skipped for Client : {client_id}------------------------\n")
            return
        icp_url = generate_apollo_url(client_id, last_page, records_required,organization)
        print(f"Apollo Search Url for the client {client_id}: {icp_url}")
        people_search_v2(icp_url, client_id, qualify_leads, index_name)  # Keeping it as a normal function
        # response = fetch_and_update_data(client_id)
        print(f"\n\n=============== Completed Data Ingestion For Organization url : {organization} ===============\n\n")

    except Exception as e:
        print(f"Error occurred while running data refresh for the organization: {organization} - {e}")

