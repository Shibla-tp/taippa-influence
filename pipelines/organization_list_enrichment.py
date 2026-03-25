import requests
import ast
import pandas as pd
from db.db_utils import retrieve_column_value, update_column_value 
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS


def construct_query_param(key, values):
    res = "&".join([f"{key}[]={value.replace(' ', '%20').replace(',', '%2C')}" for value in values])
    # print(res)
    return "&".join([f"{key}[]={value.replace(' ', '%20').replace(',', '%2C')}" for value in values])


def fetch_organization_domains(page_number):
  try:
    organization_locations = ["Europe"]
    # organization_locations = ["UAE","Quatar","United Arab Emirates"]
    organization_not_locations = ["Australia","United States"]
    # keywords=["advertising","broadcast media","media production"]
    keywords=["media buying","media planning","media strategy","ad placement","broadcast media","tv advertising","radio advertising","advertising campaigns"]
    # keywords=["insurance","media","media and broadcasting","education","automotive","finance","telecom","internet services","retail","marketing","business services"]
    # employee_size = ["300,1000000"]
    min_revenue_range = 100000000
    max_revenue_range = 5000000000
    records_required=100
    query_params = [
                        construct_query_param("organization_locations", organization_locations),
                        construct_query_param("q_organization_keyword_tags", keywords),
                        # construct_query_param("organization_num_employees_ranges", employee_size),
                        construct_query_param("organization_not_locations", organization_not_locations),
    ]
    query_params.append(f"page_number={page_number}")
    query_params.append(f"revenue_range[min]={min_revenue_range}")
    query_params.append(f"revenue_range[max]={max_revenue_range}")
    query_params.append(f"per_page={records_required}")
    base_url = "https://api.apollo.io/api/v1/mixed_companies/search"
    dynamic_url = f"{base_url}?{'&'.join(query_params)}"
    print(dynamic_url)

    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": "3DPjL0uAdul_TqcOssoBqg"
    }

    response = requests.post(dynamic_url, headers=headers)
    print(response.json())
    data = response.json()['organizations']
    print(len(data))
    # for org in data:
    #   print(org.get("primary_domain"))
    companies_domain_list = [org.get("primary_domain") for org in data if org.get("primary_domain") is not None]

    page_number = 1
    records_required = 100

    company_domain_count = {}

    for iteration in range(len(companies_domain_list)):
        organization_domains_new = companies_domain_list[iteration:iteration+1]
        domain = organization_domains_new[0]

        print(f"Processing: {domain}")
        icp_job_details = [
        'cmo','marketing head','marketing manager','chief marketing officer', 
        'vice president of sales operations', 'director of revenue operations', 
        'manager of price and yield optimization', 'product strategy manager', 
        'director of research and insights', 'ad sales finance manager'
        ]
        icp_job_seniorities = ['owner', 'founder', 'c_suite', 'partner', 'vp', 'head', 'director', 'manager', 'senior']
        query_params = [
            construct_query_param("person_titles", icp_job_details),
            construct_query_param("contact_email_status", "verified"),
            construct_query_param("q_organization_domains_list", organization_domains_new),
            construct_query_param("person_seniorities", icp_job_seniorities),
            "include_similar_titles=true",
            f"page={page_number}",
            f"per_page={records_required}"
        ]

        base_url = "https://api.apollo.io/api/v1/mixed_people/search"
        dynamic_url = f"{base_url}?{'&'.join(query_params)}"

        headers = {
            "accept": "application/json",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "x-api-key": APOLLO_API_KEY
        }

        response = requests.post(dynamic_url, headers=headers)
        data = response.json()

        profiles_count = len(data.get('people', []))
        print(f"Profiles fetched: {profiles_count}")

        # Store the result
        company_domain_count[domain] = profiles_count

    # Assuming company_domain_count is in memory already
    df = pd.DataFrame(company_domain_count.items(), columns=["Domain", "Profiles Count"])
    df.sort_values(by="Profiles Count", ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    # Filter out rows where 'Profiles Count' is 0 or missing
    df_filtered = df[df["Profiles Count"] > 0]

    # Convert 'Domain' column to a list
    organization_domain_list = df_filtered["Domain"].dropna().unique().tolist()
    print(f"Organization domain count : {len(organization_domain_list)}")
    print(f"Organization domain list : {organization_domain_list}")

    print(f"--------- Updating Client config ---------")
    existing_organization_domains = ast.literal_eval(retrieve_column_value(table_name="client_config",primary_key_col="client_id",primary_key_value="guideline",column_name="organization_domains"))
    new_organization_domains = [org for org in organization_domain_list if org not in existing_organization_domains]
    updated_organization_domains = existing_organization_domains + new_organization_domains
    update_column_value(table_name="client_config",column_name="organization_domains",column_value=updated_organization_domains,primary_key_col="client_id",primary_key_value="guideline")
  
  except Exception as e:
     print(f"Error fetching organization domains: {e}")