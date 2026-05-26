import streamlit as st
import os
from langchain.indexes import VectorstoreIndexCreator
from langchain_community.utilities import ApifyWrapper
from langchain_core.document_loaders.base import Document
from langchain_openai import OpenAI
from langchain_openai.embeddings import OpenAIEmbeddings

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

apify = ApifyWrapper()

# Function to analyze website content
def get_website_content(website_url):
    try:
        loader = apify.call_actor(
            actor_id="apify/website-content-crawler",
            run_input={"startUrls": [{"url": website_url}], "maxCrawlPages": 40},
            dataset_mapping_function=lambda item: Document(
                page_content=item["text"] or "", metadata={"source": item["url"]}
            ),
        )
        return loader
    except Exception as e:
        st.error(f"Error analyzing the website: {e}")
        return None

# Function to query indexed web content
def query_web_content(index, query):
    try:
        result = index.query_with_sources(query, llm=OpenAI())
        return {"answer": result["answer"], "source": result["sources"]}
    except Exception as e:
        st.error(f"Error querying web content: {e}")
        return None

# Page Configuration
st.set_page_config(page_title="WebInsight Analyzer", layout="centered")

# # Custom Styles
# st.markdown(
#     """
#     <style>
#         .main { text-align: center; }
#         h1 { color: #4A90E2; font-size: 30px; font-weight: bold; }
#         .stButton>button { width: 100%; border-radius: 10px; font-size: 18px; }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )
# st.markdown(
#     """
#     <style>
#         .main { text-align: center; }
#         h1 { color: #4A90E2; font-size: 30px; font-weight: bold; }
#         .stButton>button { 
#             width: 100%; 
#             border-radius: 10px; 
#             font-size: 18px;
#             transition: none;
#         }
#         .stButton>button:hover {
#             background-color: #0E1117;
#             color: #FFFFFF;
#         }
        
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

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


# Title
st.title("🌍 WebInsight Analyzer")

# Input Field
website_url = st.text_input("Enter Website URL", placeholder="https://example.com")

# Initialize session state if not already set
if "website_data" not in st.session_state:
    st.session_state.website_data = None
if "index" not in st.session_state:
    st.session_state.index = None

# Analyze Website Button
if st.button("🔍 Analyze Website"):
    if website_url:
        with st.spinner("Fetching website data..."):
            loader = get_website_content(website_url)
            if loader:
                st.session_state.website_data = loader
                st.session_state.index = VectorstoreIndexCreator(embedding=OpenAIEmbeddings()).from_loaders([loader])
                st.success("Website analysis complete! You can now query the content.")
    else:
        st.warning("Please enter a valid website URL.")

# Query Section (only appears after website is analyzed)
if st.session_state.website_data is not None and st.session_state.index is not None:
    st.divider()
    st.subheader("Query Website Content")
    query = st.text_input("Enter your query")
    
    if st.button("🔎 Search"):
        if query:
            with st.spinner("Searching..."):
                result = query_web_content(st.session_state.index, query)
                if result:
                    st.divider()
                    st.subheader("Answer")
                    st.write(result["answer"])
                    st.subheader("Source")
                    st.write(result["source"])
        else:
            st.warning("Please enter a query.")
 