
import os
import re
import openai
import json
from pyairtable import Table,Api
from pipelines.data_extractor import people_enrichment,people_enrichment_linkedin


# from db.db_utils import export_to_airtable
# from error_logger import execute_error_block

# New Airtable Configuration

AIRTABLE_BASE_ID = 'app5s8zl7DsUaDmtx'
CUR_TABLE = 'profiles_cleaned'
# LEAD_MAGNET_TABLE = 'lead_magnet_details'
LEAD_MAGNET_TABLE = 'cur_guideline'
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY', 'patPgbQSC8pAg1Gbl.19d364f069574aba976cf512ba54d63aea98b4307f50310481d0d03e20ba562f')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIRTABLE_CLEANED = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, CUR_TABLE)
# AIRTABLE_LEAD_MAGNET = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, LEAD_MAGNET_TABLE)

# def unique_key_check_airtable(column_name,unique_value,raw_table):
#     try:
#         print('Running unique key check')
#         api = Api(AIRTABLE_API_KEY)
#         airtable_obj = api.table(AIRTABLE_BASE_ID, raw_table)
#         records = airtable_obj.all()
#         print(f"\nCompleted unique key check")
#         return any(record['fields'].get(column_name) == unique_value for record in records)
#     except Exception as e:
#         print(f"Error occured in {__name__} while performing unique value check in airtable.")
def unique_key_check_airtable(column_name, unique_value, raw_table):
    try:
        airtable_obj = Table(
            AIRTABLE_API_KEY,
            AIRTABLE_BASE_ID,
            raw_table
        )

        formula = f"{{{column_name}}} = '{unique_value}'"
        records = airtable_obj.all(formula=formula)

        return len(records) > 0

    except Exception as e:
        print(f"Error in unique check: {e}")
        return False


def fetch_user_details(user_table,user_id):
    try:
        print('Fetching user information for lead magnet')
        records = user_table.all(formula=f"{{email}} = '{user_id}'")
        print(f"user_id : {user_id}")
        if records:
            print('Successfully retrieved user information')
            return {
                'id': data.get('id'),
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'name': data.get('name'),
                'email': data.get('email'),
                'linkedin_url': data.get('linkedin_url'),
                'associated_client_id': 'taippa_marketing',
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
        else:
            print("User id doesn't exist")
            return None
    except Exception as e:
        print(f"Exception occured in {__name__} while fetching user details")

# function to export data to Airtable
# def export_to_airtable(data):
#     try:
#         print(f"\n------------Exporting results to Airtable ------------")
#         api = Api(AIRTABLE_API_KEY)
#         airtable_obj = api.table(AIRTABLE_BASE_ID, LEAD_MAGNET_TABLE)
#         if unique_key_check_airtable('id',data['id'],LEAD_MAGNET_TABLE):
#             response = airtable_obj.create(data)
#             print("Record inserted successfully:", response['id'])
#         else:
#             print("Record already exists. Skipping the export...:")
#     except Exception as e:
#         print(f"Error occured in {__name__} while exporting the data to Airtable. {e}")

def export_to_airtable(data):
    try:
        print("\n------------Exporting results to Airtable ------------")

        airtable_obj = Table(
            AIRTABLE_API_KEY,
            AIRTABLE_BASE_ID,
            LEAD_MAGNET_TABLE
        )

        response = airtable_obj.create(data)
        print("Record inserted successfully:", response['id'])

    except Exception as e:
        print(f"Error exporting data to Airtable: {e}")



def collect_information(linkedin_url):
    try:
        enrichment_api_response = people_enrichment_linkedin(linkedin_url)
        if enrichment_api_response.status_code == 200:
            print(f"ernichment API successfull")
            data = enrichment_api_response.json()
            data=data['person']
            print(data)
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
            data_dict = {
                'id': data.get('id'),
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'name': data.get('name'),
                'email': data.get('email'),
                'linkedin_url': data.get('linkedin_url'),
                'associated_client_id': 'taippa_marketing',
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
            export_to_airtable(data_dict)
            return data_dict
        else:
            print(f"Error: {enrichment_api_response.status_code}, People Enrichment API failed")
            return False
    
    except Exception as e:
        print(f"Error occured during collecting information for linkedin url. {e}")
        # execute_error_block(f"Error occured during test run. {e}")

if __name__ == '__main__':
    data = collect_information('nadia@cgnet.ae')
    print(data)