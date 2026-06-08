import openai
from openai import OpenAI
import requests
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,PERPLEXITY_API_KEY
import pinecone
from openai import OpenAI
import json
from ai_modules.agents_guideline import generator_guideline
from db.db_utils import retrieve_record,update_column_value,retrieve_column_value,fetch_client_details,parse_people_info,unique_key_check_airtable,export_to_airtable,retrieve_client_tables,fetch_client_outreach_mappings,fetch_client_column
from db.db_ops import db_manager
from outreach.add_leads import add_lead_leadsin,add_lead_instantly

openai.api_key = OPENAI_API_KEY

def execute_outreach_sequence():
    try:
        lead_info_outreach = db_manager.get_record("outreach_guideline","status","Approved")
        print(f"\n-------------------------Lead info--------------------------------\n {lead_info_outreach}\n")
        apollo_id = lead_info_outreach.get("apollo_id")
        print(f"apollo_id: {apollo_id}")
        client_config = retrieve_record("client_config","client_id",lead_info_outreach.get("associated_client_id")).get('fields')
        cur_table_name = client_config.get('cleaned_table')
        lead_info_curated = db_manager.get_record(cur_table_name,"apollo_id",apollo_id)        
        outreach_table_name = client_config.get('outreach_table')
        target_region = lead_info_outreach.get("target_region")
        outreach_index = int(client_config.get("outreach_index"))

        if outreach_index == 1:
            instantly_campaign_id = "2441391c-e88d-498d-86ce-f5e10e7018bf"
            linkedin_campaign_id = "318190"
            account_id = "Mag"
        elif outreach_index == 2:
            instantly_campaign_id = "2441391c-e88d-498d-86ce-f5e10e7018bf"
            linkedin_campaign_id = "330748"
            account_id = "Sravan"
        elif outreach_index == 3:
            instantly_campaign_id = "2441391c-e88d-498d-86ce-f5e10e7018bf"
            linkedin_campaign_id = "330753"
            account_id = "Urmi"
        # elif outreach_index == 4 :  
        #     instantly_campaign_id = "2441391c-e88d-498d-86ce-f5e10e7018bf"
        #     linkedin_campaign_id = "333714"
        linkedin_campaign_id = "326358"
        print(f"apollo_id: {apollo_id}, account_id: {account_id}, LinkedIn campaign_id: {linkedin_campaign_id}, Outreach table: {outreach_table_name}")
        status = add_lead_leadsin(apollo_id,linkedin_campaign_id,outreach_table_name)
        print(f"Lead added to LeadsIn campaign status: {status}")
        
        payload = {
        "campaign": instantly_campaign_id,
        "first_name": lead_info_outreach.get('recipient_first_name'),
        "last_name": lead_info_outreach.get('recipient_last_name'),
        "email": lead_info_outreach.get('recipient_email'),
        "personalization": lead_info_outreach.get('email_message_1'),
        "custom_variables": {
            "Subject": lead_info_outreach.get('linkedin_subject'),
            "FollowUpEmail": lead_info_outreach.get('email_message_2'),
        }
        }
        status = add_lead_instantly(payload)
        print(f"Lead added to Instantly campaign status: {status}")

        update_fields = {
            "apollo_id": lead_info_outreach.get("apollo_id"),
            "status": "Active"
        }

        db_manager.update_multiple_fields("outreach_guideline", update_fields, "apollo_id")
        print(f"Outreach table updated successfully")
        filter_cols= ["thread_id"]
        filter_values = [client_config.get("campaign_name")+"_"+lead_info_outreach.get("apollo_id")]
        linkedin_leads_record = db_manager.get_record("linkedin_leads", "thread_id", client_config.get("campaign_name")+"_"+lead_info_outreach.get("apollo_id"))
        print(f"LinkedIn leads duplicate record found: {linkedin_leads_record}")
        linkedin_leads_data = None
        if linkedin_leads_record is None:
            linkedin_leads_data = {
                "thread_id": client_config.get("campaign_name")+"_"+lead_info_outreach.get("apollo_id"),
                "campaign_name": client_config.get("campaign_name"),
                "apollo_id": lead_info_outreach.get("apollo_id"),
                "linkedin_profile_url": lead_info_outreach.get("linkedin_profile_url"),
                "full_name": lead_info_curated.get("full_name"),
                "email": lead_info_outreach.get("recipient_email"),
                "picture": lead_info_curated.get("picture"),
                "status": "Yet To Connect",
                "company": lead_info_outreach.get("recipient_company"),
                "message": lead_info_outreach.get("linkedin_message"),
                "message_2": lead_info_outreach.get("linkedin_message_2"),
                "connection_message": lead_info_outreach.get("linkedin_connection_message"),
                "subject": lead_info_outreach.get("linkedin_subject"),
            }
            db_manager.insert_data("linkedin_leads", linkedin_leads_data)
            # db_manager.update_multiple_fields("linkedin_leads",update_fields,"thread_id")     
            print(f"Added LinkedIn leads entry to the table successfully")
        
        updated_outreach_index = outreach_index + 1 if outreach_index != 3 else 1
        update_column_value(
                    table_name="client_config", 
                    column_name="outreach_index",
                    column_value=str(updated_outreach_index),
                    primary_key_col="client_id",
                    primary_key_value=lead_info_outreach.get("associated_client_id")
        )
        outreach_status = {
            "status":"Success",
            "message":"Successfully generated the outreach content",
            "updated_fields": update_fields
        }

    except Exception as e:
        print(f"Error in execute_outreach_sequence: {e}")
        outreach_status = {
            "status": "Error",
            "message": f"Error occured in execute_outreach_sequence: {e}",
            "updated_fields": {}
        }

    return outreach_status