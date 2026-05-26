import streamlit as st
import requests
from app.pipelines.lead_website_analysis import query_web_content,get_website_content
# Page Configurations
st.set_page_config(page_title="Generate - Smart Miner", page_icon="🌍", layout="centered")

# Custom CSS to Remove Hover and Focus Effects Completely
st.markdown("""
    <style>
    body {
        background-color: #121212;
        color: #e0e0e0;
    }
    .main {
        background-color: #121212;
    }
    h1, p {
        text-align: center;
        color: #ffffff;
    }
    
    /* Input box styling */
    .stTextInput > div {
        transition: none !important; /* Disables any hover transition */
    }
    .stTextInput > div > div {
        border: 1px solid #333 !important;
        background-color: #1e1e1e !important;
    }
    .stTextInput > div > div > input {
        font-size: 18px;
        padding: 12px;
        border-radius: 6px;
        border: 1px solid #333 !important;
        background-color: #1e1e1e !important;
        color: #e0e0e0 !important;
        outline: none !important; /* Removes default focus outline */
    }

    /* Remove hover effect (background and border should stay unchanged) */
    .stTextInput > div:hover,
    .stTextInput > div > div:hover,
    .stTextInput > div > div:focus-within {
        border: 1px solid #333 !important;
        background-color: #1e1e1e !important;
        box-shadow: none !important;
    }

    /* Remove red hover effect appearing outside the input box */
    .stTextInput > div:has(input:focus),
    .stTextInput > div:has(input:hover) {
        border: 1px solid #333 !important;
        background-color: #1e1e1e !important;
        box-shadow: none !important;
    }

    /* Button styling */
    .stButton > button {
        background-color: #1db954;
        color: black;
        font-size: 18px;
        padding: 10px 20px;
        border-radius: 6px;
        border: none;
        transition: none !important;
    }
    
    /* Button should not change color on hover */
    .stButton > button:hover {
        background-color: #1db954 !important;
    }

    .stTextInput > div > div > input::placeholder {
        color: #777 !important;
    }
    </style>
""", unsafe_allow_html=True)

# App title and description
st.markdown("<h1>🤖🌐 AI-Smart Miner</h1>", unsafe_allow_html=True)
# st.markdown("<p>Drop your LinkedIn profile and client name below to begin!</p>", unsafe_allow_html=True)

# Form Layout
with st.form("linkedin_form"):
    linkedin_url = st.text_input("LinkedIn URL", placeholder="https://www.linkedin.com/in/your-profile")
    client_id = st.text_input("Client", placeholder="berkleys_homes")
    submit_button = st.form_submit_button("Submit")
    
    

# Handling form submission
if submit_button:
    # response = requests.get(
    #             f"https://magmostafa.pythonanywhere.com/demo_test?linkedin_url={linkedin_url}&client_id={client_id}"
    #             )
    try:
        # response = requests.get(
        #                 f"http://127.0.0.1:5000/demo_test?linkedin_url={linkedin_url}&client_id={client_id}"
        #             )
        response = requests.get(
                f"https://magmostafa.pythonanywhere.com/demo_test?linkedin_url={linkedin_url}&client_id={client_id}"
                )
        if response.status_code == 200:
            st.success(f"📧 We'll be sending you a personalized email shortly.")
        else:
            st.error("⚠️ Oops! It looks like our server is currently busy. Please try again later.")
    except Exception as e:
        st.error("⚠️ Oops! It looks like our server is currently busy. Please try again later.")