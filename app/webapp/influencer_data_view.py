import streamlit as st
from pyairtable import Table
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

# Airtable credentials from environment variables
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

# Inject custom CSS for white table background and blue text for tags
st.markdown("""
    <style>
    .dataframe tbody tr th,
    .dataframe tbody tr td {
        background-color: white !important;
        color: black;
    }

    .dataframe thead tr th {
        background-color: #f0f0f0 !important;
        color: black;
    }

    /* Optional: Target specific column called "tags" and color it blue */
    td:nth-child(n):has(span:contains("tags")),
    td:has(span[title="tags"]) {
        color: blue !important;
    }

    /* General style to make tag-like entries blue */
    td {
        color: #1e90ff; /* DodgerBlue */
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Airtable table
table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "src_influencer_data")

# Fetch all records
@st.cache_data
def fetch_data():
    records = table.all()
    data = [record['fields'] for record in records]
    return pd.DataFrame(data)

# Load data
df = fetch_data()

st.title("Airtable Explorer")


# if df.empty:
#     st.warning("No data found in Airtable.")
# else:
#     # Sidebar Filters
#     with st.sidebar:
#         st.header("Filters")
#         for column in df.columns:
#             if df[column].dtype == object and df[column].nunique() < 20:
#                 selected = st.multiselect(f"{column}", options=df[column].dropna().unique(), default=df[column].dropna().unique())
#                 df = df[df[column].isin(selected)]

#     st.write("### Filtered Data")
#     st.dataframe(df.reset_index(drop=True))
