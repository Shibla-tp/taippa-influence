import requests
import openai
import os
from datetime import datetime
from db.db_utils import fetch_client_details,parse_people_info,unique_key_check_airtable,export_to_airtable,retrieve_client_tables,fetch_client_outreach_mappings,fetch_client_column
from pipelines.lead_qualifier import qualify_lead
from pipelines.data_sanitization_psql import sanitize_data
from error_logger import execute_error_block
from db.db_ops import db_manager
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS
# from lead_magnet.industry_insights import get_cold_email_kpis

CLIENT_DETAILS_TABLE_NAME = os.getenv("CLIENT_DETAILS_TABLE_NAME")
CLIENT_INFO_TABLE_NAME = os.getenv("CLIENT_INFO_TABLE_NAME")

def people_enrichment_v2(apollo_id):
    try:
        url = f"https://api.apollo.io/api/v1/people/match?id={apollo_id}&reveal_personal_emails=true&reveal_phone_number=false&webhook_url=https%3A%2F%2Fmagmostafa.pythonanywhere.com%2Fapollo_webhook"
        response = requests.post(url, headers=APOLLO_HEADERS)
        # print(f"Extracting phone numbers via people enrichment")
        return response
        
    except Exception as e:
        print(f"Error occured during people enrichment for the apollo_id {apollo_id}")

def people_enrichment(apollo_id):
    try:
        print(f"\n------------Started Persona Data Enrichment------------")
        url = f"https://api.apollo.io/api/v1/people/match?id={apollo_id}&reveal_personal_emails=false&reveal_phone_number=false"
        response = requests.post(url, headers=APOLLO_HEADERS)
        # print(response.json())
        print(f"------------Completed Persona Data Enrichment------------")
        return response
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} for the data enrichment layer. {e}")

def people_enrichment_linkedin(linkedin_url):
    try:
        print(f"\n------------Started Persona Data Enrichment------------")
        # url = "https://api.apollo.io/api/v1/people/match?linkedin_url=https%3A%2F%2Fwww.linkedin.com%2Fin%2Fmagmostafa%2F&reveal_personal_emails=false&reveal_phone_number=false"
        url = f"https://api.apollo.io/api/v1/people/match?linkedin_url={linkedin_url}&reveal_personal_emails=true&reveal_phone_number=false"
        # url = f"https://api.apollo.io/api/v1/people/match?id={apollo_id}&reveal_personal_emails=false&reveal_phone_number=false"
        response = requests.post(url, headers=APOLLO_HEADERS)
        print(f"------------Completed Persona Data Enrichment------------")
        return response
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} for the data enrichment layer. {e}")

def segregate_region(region):
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in geography. Respond only with one of the following tags: europe, asia, north_america, south_america, australia, or other."},
                {"role": "user", "content": f"Classify the region '{region}' into one of the following: europe, middle_east, asia, africa, north_america, australia, or other. Respond with only the tag."}
            ],
            temperature=0,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error occured while segregating region: {e}")
        return "other"

def people_search_v2(search_url,client_id,qualify_leads,index_name):
  try:
    print(f"\n---------- Started Persona Data Mining for client : {client_id} ----------")
    print(f"Search url: {search_url}")
    print(f"Headers: {APOLLO_HEADERS}")
    response = requests.post(search_url, headers=APOLLO_HEADERS)
    print(f"Execution status code: {response.status_code}")
    if response.status_code == 200:
        print(f"\n ---------- Completed Persona Data Mining for client : {client_id} ----------")
        data = response.json()
        print(f"Data collected: {data.keys()}")
        print(f"Data Contacts: {data['contacts']}")
        print(f"Data People: {data['people']}")

        print(f"No of profiles collected : {len(data['people'])}")
        profiles_found = len(data['people'])
        enriched_profiles=0
        selected_profiles=0
        iteration=1
        print(f"\n\n---------- Starting the People Search Iteration ----------\n\n")
        ingested_apollo_ids = []
        for contact in data['people']:
            print(f"\n---------- People Search Iteration {iteration} for client_id {client_id} ----------\n")
            iteration += 1
            apollo_id = contact['id']    
            print(f"------------Data ingestion started for record id :{apollo_id}, for client_id :{client_id} ------------")
            # raw_table,cleaned_table,outreach_table = retrieve_client_tables(client_id)
            info_details = db_manager.get_record(CLIENT_INFO_TABLE_NAME,"client_id",client_id)
            raw_table,cleaned_table,outreach_table = info_details.get('raw_table'),info_details.get('cleaned_table'),info_details.get('outreach_table')
            print("\n******-----------------------Raw Table:----------------------------******\n", raw_table)
            # record_exists = unique_key_check_airtable('apollo_id',apollo_id,raw_table)   
            record_exists = db_manager.unique_key_check('apollo_id', apollo_id, raw_table)
            if record_exists:
                print(f'Record with the following id: {apollo_id} already exists. Skipping the entry...')
                continue   
            
            enrichment_api_response = people_enrichment_v2(apollo_id)
            enriched_profiles+=1
            if enrichment_api_response.status_code == 200:
                data = enrichment_api_response.json()
                data=data['person']
                # print({f"Data Person:{data}"})
                client = openai.OpenAI(api_key=OPENAI_API_KEY)
                response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at text summarization."},
                    {"role": "user", "content": f"Please shorten this description: {data['employment_history']}"}
                ],
                )
                employment_summary = response.choices[0].message.content
                target_region = segregate_region(data.get('organization').get('country') if data.get('organization') else '')
                timestamp = datetime.now()
                data_dict = {
                    'apollo_id': data.get('apollo_id'),
                    'first_name': data.get('first_name'),
                    'last_name': data.get('last_name'),
                    'name': data.get('name'),
                    'email': data.get('email'),
                    'linkedin_url': data.get('linkedin_url'),
                    'associated_client_id': client_id,
                    'title': data.get('title'),
                    'seniority': data.get('seniority'),
                    'headline': data.get('headline'),
                    'is_likely_to_engage': 'True',
                    'photo_url': data.get('photo_url'),
                    'email_status': data.get('email_status'),
                    'twitter_url': data.get('twitter_url'),
                    'employment_history': str(data.get('employment_history')),
                    'employment_summary':str(employment_summary),
                    'organization_name': data.get('organization').get('name'),
                    'organization_website': data.get('organization').get('website_url') if data.get('organization') else '',
                    'organization_linkedin': data.get('organization').get('linkedin_url') if data.get('organization') else '',
                    'organization_facebook': data.get('organization').get('facebook_url') if data.get('organization') else '',
                    'organization_primary_phone': str(data.get('organization').get('primary_phone')) if data.get('organization') else '',
                    'organization_logo': data.get('organization').get('logo_url') if data.get('organization') else '',
                    'organization_primary_domain': data.get('organization').get('primary_domain') if data.get('organization') else '',
                    'organization_industry': data.get('organization').get('industry') if data.get('organization') else '',
                    'organization_estimated_num_employees': str(data.get('organization').get('estimated_num_employees')) if data.get('organization') else '',
                    'organization_phone': data.get('organization').get('phone') if data.get('organization') else '',
                    'organization_city': data.get('organization').get('city') if data.get('organization') else '',
                    'organization_state': data.get('organization').get('state') if data.get('organization') else '',
                    'organization_country': data.get('organization').get('country') if data.get('organization') else '',
                    'organization_short_description': data.get('organization').get('short_description') if data.get('organization') else '',
                    'organization_technology_names': str(data.get('organization').get('technology_names')) if data.get('organization') else '',
                    'created_time':str(timestamp),
                    'filter_criteria':"generic",
                    'target_region': target_region,
                }

                if qualify_leads=='yes':
                    qualification_status = qualify_lead(apollo_id,data_dict,index_name)
                    if not qualification_status:
                        print(f"\n------------Lead Disqualified------------")
                        print('Skipping the entry...')
                        continue
                    print(f"\n------------Lead Qualified------------")
                else:
                    print(f"Skipping lead qualification...")
                    # continue
                print("Data Dictionary:",data_dict)
                db_manager.insert_data_collection(data_dict)
                
                # db_manager.insert_data(data_dict,raw_table)
                # export_to_airtable(data_dict,raw_table)
                print(f"Data collected in source table")
                response = sanitize_data(client_id,data_dict)
                print(f"Data sanitized and uploaded to outreach table")
                ingested_apollo_ids.append(apollo_id)
                selected_profiles+=1
                print(f"\n------------Data ingestion successful for record id :{apollo_id}, client_id : {client_id}------------\n")
            else:
                print(f"Error: {enrichment_api_response.status_code}, People Enrichment API failed")
                return False
        print('\n ================= Completed Data Collection, Initiating Data Cleaning ==================\n')
        print(f"Total profiles found: {profiles_found}")
        print(f"Total profiles enriched: {enriched_profiles}")
        print(f"Total profiles uploaded: {selected_profiles}")
        return selected_profiles,ingested_apollo_ids  
    else:
        print(f"\n------------ ERROR : Persona Search API Failed ------------")
        return False
  except Exception as e:
    execute_error_block(f"Error occured in {__name__} during data ingestion. {e}")

def manual_data_insertion(records_list,qualify_leads,client_id,index_name):
    try:
        print(f"\n------------Started Manual Data Ingestion------------")
        raw_table,cleaned_table,outreach_table = retrieve_client_tables(client_id)
        for record in records_list:
            record_exists = unique_key_check_airtable('apollo_id',record['apollo_id'],raw_table)
            if record_exists:
                print(f'Record with the following id: {record["apollo_id"]} already exists. Skipping the entry...')
                continue
            apollo_id = record['apollo_id']
            if qualify_leads=='yes':
                    qualification_status = qualify_lead(apollo_id,record,index_name)
                    if not qualification_status:
                        print(f"\n------------Lead Disqualified------------")
                        print('Skipping the entry...')
                        continue
                    print(f"\n------------Lead Qualified------------")
            else:
                print(f"Skipping lead qualification...")
            record.pop('id')
            # print(record)
            export_to_airtable(record,raw_table)
            print(f"\n------------Data ingestion successful for record id :{record['apollo_id']}------------")
        print(f"\n------------Completed Manual Data Ingestion------------")
    except Exception as e:
        execute_error_block(f"Error occured during manual data ingestion. {e}")

def test_run_pipeline(test_run_id,client_id):
    try:
        raw_table,cleaned_table,outreach_table = retrieve_client_tables(client_id)
        record_exists = unique_key_check_airtable('apollo_id',test_run_id,raw_table)
        if record_exists:
            print(f'Record with the following id: {test_run_id} already exists. Skipping the entry...')
            return True
        enrichment_api_response = people_enrichment_linkedin(test_run_id)
        if enrichment_api_response.status_code == 200:
            data = enrichment_api_response.json()
            data=data['person']
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # or "gpt-4" for more advanced results
                messages=[
                    {"role": "system", "content": "You are an expert at text summarization."},
                    {"role": "user", "content": f"Please shorten this description: {data['employment_history']}"}
                ],
                max_tokens=100  # Adjust based on the desired length of the output
                )
            employment_summary = response['choices'][0]['message']['content']
            data_dict = {
                    'apollo_id': data['id'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'name': data['name'],
                    'email': 'sravan.workemail@gmail.com',
                    'linkedin_url': data['linkedin_url'],
                    'associated_client_id': client_id,
                    'title': data['title'],
                    'seniority': data['seniority'],
                    'headline': data['headline'],
                    'is_likely_to_engage': 'True',
                    'photo_url': data['photo_url'],
                    'email_status': "verified",
                    'twitter_url': data['twitter_url'],
                    'github_url': data['github_url'],
                    # 'facebook_url': data['facebook_url'],
                    'employment_history': str(data['employment_history']),
                    'employment_summary':str(employment_summary),
                    'organization_name': data['organization']['name'],
                    'organization_website': data['organization']['website_url'],
                    'organization_linkedin': data['organization']['linkedin_url'],
                    # 'organization_facebook': data['organization']['facebook_url'],
                    'organization_primary_phone': str(data['organization']['primary_phone']),
                    'organization_logo': data['organization']['logo_url'],
                    'organization_primary_domain': data['organization']['primary_domain'],
                    'organization_industry': data['organization']['industry'],
                    'organization_estimated_num_employees': str(data['organization']['estimated_num_employees']),
                    'organization_phone': data['organization']['phone'],
                    'organization_city': data['organization']['city'],
                    'organization_state': data['organization']['state'],
                    'organization_country': data['organization']['country'],
                    'organization_short_description': data['organization']['short_description'],
                    'organization_technology_names': str(data['organization']['technology_names'])
            }
            data_dict = {
                    'apollo_id': data.get('id'),
                    'first_name': data.get('first_name'),
                    'last_name': data.get('last_name'),
                    'name': data.get('name'),
                    # 'email': data.get('email'),
                    'email': 'sravzone@gmail.com',
                    'linkedin_url': data.get('linkedin_url'),
                    'associated_client_id': client_id,
                    'title': data.get('title'),
                    'seniority': data.get('seniority'),
                    'headline': data.get('headline'),
                    'is_likely_to_engage': 'True',
                    'photo_url': data.get('photo_url'),
                    'email_status': data.get('email_status'),
                    'twitter_url': data.get('twitter_url'),
                    'github_url': data.get('github_url'),
                    'facebook_url': data.get('facebook_url'),
                    'employment_history': str(data.get('employment_history')),
                    'employment_summary':str(employment_summary),
                    'organization_name': data.get('organization').get('name'),
                    'organization_website': data.get('organization').get('website_url') if data.get('organization') else '',
                    'organization_linkedin': data.get('organization').get('linkedin_url') if data.get('organization') else '',
                    'organization_facebook': data.get('organization').get('facebook_url') if data.get('organization') else '',
                    'organization_primary_phone': str(data.get('organization').get('primary_phone')) if data.get('organization') else '',
                    'organization_logo': data.get('organization').get('logo_url') if data.get('organization') else '',
                    'organization_primary_domain': data.get('organization').get('primary_domain') if data.get('organization') else '',
                    'organization_industry': data.get('organization').get('industry') if data.get('organization') else '',
                    'organization_estimated_num_employees': str(data.get('organization').get('estimated_num_employees')) if data.get('organization') else '',
                    'organization_phone': data.get('organization').get('phone') if data.get('organization') else '',
                    'organization_city': data.get('organization').get('city') if data.get('organization') else '',
                    'organization_state': data.get('organization').get('state') if data.get('organization') else '',
                    'organization_country': data.get('organization').get('country') if data.get('organization') else '',
                    'organization_short_description': data.get('organization').get('short_description') if data.get('organization') else '',
                    'organization_technology_names': str(data.get('organization').get('technology_names')) if data.get('organization') else ''
                }
            export_to_airtable(data_dict,raw_table)
            print(f"\n------------Data ingestion successful for record id :{test_run_id}------------")
            return 1
        else:
            print(f"Error: {enrichment_api_response.status_code}, People Enrichment API failed")
            return False
    
    except Exception as e:
        execute_error_block(f"Error occured during test run. {e}")

def run_demo_pipeline(linkedin_url,client_id,outreach_table):
    try:
        client_mappings = fetch_client_outreach_mappings(client_id)
        enrichment_api_response = people_enrichment_linkedin(linkedin_url)
        if enrichment_api_response.status_code == 200:
            data = enrichment_api_response.json()
            data=data['person']
            # response = openai.ChatCompletion.create(
            #     model="gpt-3.5-turbo",  # or "gpt-4" for more advanced results
            #     messages=[
            #         {"role": "system", "content": "You are an expert at text summarization."},
            #         {"role": "user", "content": f"Please shorten this description: {data['employment_history']}"}
            #     ],
            #     max_tokens=100  # Adjust based on the desired length of the output
            #     )
            # employment_summary = response['choices'][0]['message']['content']
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at text summarization."},
                    {"role": "user", "content": f"Please shorten this description: {data['employment_history']}"}
                ],
            )
            
            # employment_summary = response['choices'][0]['message']['content']
            employment_summary = response.choices[0].message.content
            unique_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data_dict = {
                    'apollo_id': unique_id,
                    'recipient_first_name': data.get('first_name'),
                    'recipient_last_name': data.get('last_name'),
                    'recipient_role': data.get('title'),
                    'recipient_company': data.get('organization').get('name'),
                    'recipient_company_website': data.get('organization').get('website_url') if data.get('organization') else '',
                    'recipient_bio': data.get('headline'),
                    'recipient_email': 'sravan.workemail@gmail.com',
                    "sender_name": client_mappings.get("full_name"),
                    "sender_title": client_mappings.get("job_title"),
                    "sender_company": client_mappings.get("company_name"),
                    "sender_email": client_mappings.get("email"),
                    "sender_company_website": client_mappings.get("company_website"),
                    "key_benefits": client_mappings.get("solution_benefits"),
                    "unique_features": client_mappings.get("unique_features"),
                    "impact_metrics": client_mappings.get("solution_impact_examples"),
                    "cta_options": client_mappings.get("cta_options"),
                    "color_scheme": client_mappings.get("color_scheme"),
                    "font_style": client_mappings.get("font_style"),
                    "linkedin_profile_url":data.get('linkedin_url'),
                    "unique_id":"NA",
                    "associated_client_id":client_id,
                    "employment_summary":employment_summary,
                    "instantly_campaign_id": client_mappings.get("instantly_campaign_id"),
                    "business_type": client_mappings.get("business_type"),
                    "outreach_table": client_mappings.get("outreach_table")
                }
            export_to_airtable(data_dict,outreach_table)
            print(f"\n------------Data ingestion successful for record id :{unique_id}------------")
            return 1
        else:
            print(f"Error: {enrichment_api_response.status_code}, People Enrichment API failed")
            return False
    
    except Exception as e:
        execute_error_block(f"Error occured during demo run. {e}")