import streamlit as st
import requests
import re
import sys
from urllib.parse import quote

# Custom CSS for styling
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(to right, #1e3c72, #2a5298);
        font-family: 'Poppins', sans-serif;
        color: #ffffff;
    }
    .sidebar .sidebar-content {
        background: #ffffff;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
    }
    .main-title {
        text-align: center;
        color: #ffffff;
        font-size: 40px;
        font-weight: 700;
        margin-top: 20px;
    }
    .sub-title {
        color: #dcdde1;
        font-size: 22px;
        margin-bottom: 10px;
    }
    .filters {
        background: rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 0 15px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }
    .stTextInput > div > div > input {
        background: #ffffff;
        color: #333;
        border: none;
        border-radius: 5px;
        padding: 10px;
    }
    .footer {
        text-align: center;
        margin-top: 50px;
        color: #bdc3c7;
        font-size: 14px;
    }
    .stButton > button {
        background: #6c63ff;
        color: #ffffff;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
    }
    .stButton > button:hover {
        background: #5146d9;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def execute_error_block(error_message):
    print('============== ERROR BLOCK ==============')
    print(error_message)
    print(f"\n------------Stopping the program ------------")
    sys.exit()

def validate_employee_ranges(organization_num_employees_ranges):
    try:
        # if re.match(r'^\[(\d+,\s*\d+)\](,\[(\d+,\s*\d+)\])*?$',organization_num_employees_ranges):
        if re.match(r'^\[(\d+,\s*\d+)\](,\s*\[(\d+,\s*\d+)\])*?$',organization_num_employees_ranges):
            ranges_list = [item.strip() for item in organization_num_employees_ranges.split(",")]
            # st.write("Parsed Ranges:", ranges_list)
            return True
        else:
            st.error("Invalid format for employee range! Please use the format: [1,10],[11,20],[21,50]")
            return False
    except Exception as e:
        execute_error_block(f"Error occured while validating the employee range. {e}")

def validate_fields(job_titles,person_seniorities,person_locations,organization_locations,organization_num_employees_ranges):
    try:
        return True
        return validate_employee_ranges(organization_num_employees_ranges) 
    except Exception as e:
        execute_error_block(f"Error occured while validating the fields. {e}")

# Title and Description
st.markdown('<div class="main-title">Generate - Smart Data Miner </div>', unsafe_allow_html=True)

# st.write("Use the filters below to customize the extraction of leads.")
from streamlit_tags import st_tags

# Input for job titles
job_titles = st_tags(
    label="Job titles",
    text="Press Enter to add more",
    suggestions=["ceo","cmo","cfo","coo","marketing manager", "marketing director", "sales executive", "data scientist"],
    key="job_titles"
)
job_titles=",".join(job_titles)

person_seniorities = st_tags(
    label="Person seniorities",
    text="Press Enter to add more",
    suggestions=["owner", "founder", "director"],
    key="person_seniorities"
)
person_seniorities=",".join(person_seniorities)

person_locations = st_tags(
    label="Person locations",
    text="Press Enter to add",
    suggestions=["Dubai, United Arab Emirates","India","United Kingdom","Russia","Saudi Arabia","United States","Quatar"],
    key="person_locations"
)


organization_locations = st_tags(
    label="Organization locations",
    text="Press Enter to add",
    suggestions=["Dubai, United Arab Emirates","India","United Kingdom","Russia","Saudi Arabia","United States","Quatar"],
    key="organization_locations"
)

email_status = 'verified,likely to engage'

organization_num_employees_ranges = st_tags(
    label="Organization employees range",
    text="Press Enter to add",
    suggestions=["1,10","20,50","100,200","1,100000"],
    key="organization_num_employees_ranges"
)

# organization_num_employees_ranges = [[int(x) for x in range.split(",")] for range in organization_num_employees_ranges]
# organization_num_employees_ranges = str(organization_num_employees_ranges)[1:-1]
print(f"organization_num_employees_ranges: {organization_num_employees_ranges}")

# q_keywords = st.text_input("Keywords","") 

q_keywords = st_tags(
    label="Keywords",
    text="Press Enter to add",
    suggestions=["finance","invest"],
    key="q_keywords"
)

# q_keywords = st.text_input(
#     label="Keywords",
#     placeholder="Enter keywords separated by commas",
#     key="q_keywords"
# )

page_number = str(st.number_input(
    label="Page number",
    min_value=1, 
    value=1, 
    step=1,   
    format="%d"  
))

results_per_page = str(st.number_input(
    label="Results per page",
    min_value=1, 
    value=10,  
    step=1,    
    format="%d"  
))

client_id = str(st.selectbox(
    label="Client id", 
    options=["berkleys_homes", "berkleys_homes_test", "taippa_marketing","plot_taippa"],
    index=1
))

server_test = st.radio("Test in server:", options=["yes", "no"], index=1)
test_run = st.radio("Test run:", options=["yes", "no"], index=1)
search_via_url = st.radio("Custom search via url:", options=["yes", "no"], index=1)
qualify_leads = st.radio("Qualify leads:", options=["yes", "no"], index=0)
test_run_id=''
if test_run=="yes":
    test_run_id = st.text_input("LinkedIn url:", "https://www.linkedin.com/in/isravanbr/")

custom_search_url=""
if search_via_url =="yes":
    custom_search_url = st.text_input(
    label="Custom Seach Url",
    value="https://api.apollo.io/api/v1/mixed_people/search?person_titles[]=Facilities%20director&person_titles[]=COO&person_titles[]=CEO&person_titles[]=operations%20director&person_titles[]=director%20of%20operations&person_locations[]=&organization_locations[]=United%20Arab%20Emirates&contact_email_status[]=verified&organization_num_employees_ranges[]=500%2C10000&page=11&per_page=40",  # Default value
    max_chars=3000  # Optional: Limit the number of characters
    )
st.markdown('</div>', unsafe_allow_html=True)

if st.button("Fetch Data"):
    print('----------------Fields Validation--------------------')
    validation_status = validate_fields(
        job_titles=job_titles,
        person_seniorities=person_seniorities,
        person_locations=person_locations,
        organization_locations=organization_locations,
        organization_num_employees_ranges=organization_num_employees_ranges
        )
    print(f"Fields validation status : {validation_status}")
    if custom_search_url!="" or validation_status:
        st.write("Valid Input")
        custom_search_url = quote(custom_search_url, safe='')
        if server_test == "yes":
            response = requests.get(
                    f"https://magmostafa.pythonanywhere.com/data_ingestion?page={page_number}&per_page={results_per_page}&job_titles={job_titles}&person_seniorities={person_seniorities}&person_locations={person_locations}&organization_locations={organization_locations}&email_status={email_status}&organization_num_employees_ranges={organization_num_employees_ranges}&client_id={client_id}&test_run_id={test_run_id}&qualify_leads={qualify_leads}&q_keywords={q_keywords}&custom_search_url={custom_search_url}"
                )
        else:
            print(f"Encoded custom search url: {custom_search_url}")
            response = requests.get(
                    f"http://127.0.0.1:5000/data_ingestion?page={page_number}&per_page={results_per_page}&job_titles={job_titles}&person_seniorities={person_seniorities}&person_locations={person_locations}&organization_locations={organization_locations}&email_status={email_status}&organization_num_employees_ranges={organization_num_employees_ranges}&client_id={client_id}&test_run_id={test_run_id}&qualify_leads={qualify_leads}&q_keywords={q_keywords}&custom_search_url={custom_search_url}"
                )
        print(response)
        print('-------COMPLETED-----------')
        if response.status_code == 200:
            st.write("Data Miner completed successfully!")
            st.write(response.json()['Status'])  
        else:
            st.write(response)
            st.error("Failed to fetch data.")

# # Adding an image to the sidebar
# st.sidebar.image(
#     "logo.JPG",  
#     caption="",  
#     use_column_width=True
# )

st.sidebar.markdown("<br>", unsafe_allow_html=True) 

st.sidebar.markdown('<div class="sub-title">Filters Applied</div>', unsafe_allow_html=True)
st.sidebar.write("**Page Number:**", page_number)
st.sidebar.write("**Results per Page:**", results_per_page)
st.sidebar.write("**Job Titles:**", job_titles)
st.sidebar.write("**Person Seniorities:**", person_seniorities)
st.sidebar.write("**Person Locations:**", person_locations)
st.sidebar.write("**Organization Locations:**", organization_locations)
st.sidebar.write("**Email Status:**", email_status)
st.sidebar.write("**Organization Employee Ranges:**", organization_num_employees_ranges)

# Footer
st.markdown('<div class="footer">Generate | AI Powered Lead Generation System</div>', unsafe_allow_html=True)

# https://api.apollo.io/api/v1/mixed_people/search?person_titles[]=Facilities%20director&person_titles[]=COO&person_titles[]=CEO&person_titles[]=operations%20director&person_titles[]=director%20of%20operations&person_locations[]=&organization_locations[]=United%20Arab%20Emirates&contact_email_status[]=verified&organization_num_employees_ranges[]=500%2C10000&page={page_number}&per_page={records_required}
