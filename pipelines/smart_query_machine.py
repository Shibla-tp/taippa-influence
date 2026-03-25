
import pandas as pd
from docx import Document
import pdfplumber
import openai, pinecone, pandas as pd, sqlite3
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from PIL import Image
import pytesseract
import os
import ast
import requests
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,PINECONE_API_KEY

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
def extract_text_from_excel(path):
    try:
        df = pd.read_excel(path)
        # Concatenate all cell values as strings
        text = ""
        for col in df.columns:
            text += " ".join(df[col].astype(str).tolist()) + "\n"
        return text
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return ""

def extract_text_from_docx(path):
    try:
        doc = Document(path)
        return "\n".join([para.text for para in doc.paragraphs if para.text])
    except Exception as e:
        print(f"Error reading Word: {e}")
        return ""

def extract_text_from_pdf(path):
    try:
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def extract_text_from_image(path):
    try:
        img = Image.open(path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"Error reading image: {e}")
        return ""


FILE_HANDLERS = {
".xlsx": extract_text_from_excel,
".xls": extract_text_from_excel,
".docx": extract_text_from_docx,
".doc": extract_text_from_docx,
".pdf": extract_text_from_pdf,
}


def download_file_from_drive(drive_url: str, output_path: str, chunk_size=32768):
    """Downloads a file from a direct Drive URL to a local file path."""
    response = requests.get(drive_url, stream=True)
    response.raise_for_status()  # Will raise HTTPError if failed
    with open(output_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                file.write(chunk)
    print(output_path)
    return output_path

def process_file(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in FILE_HANDLERS:
        raise ValueError(f"Unsupported file type: {ext}")
    handler_function = FILE_HANDLERS[ext]
    return handler_function(filepath)


def process_documents(files,client_id):
    try:
        text= ""
        for file in files:
            text+= process_file(file) + "\n"

        print(f"Creating Pinecone index and embedding the document...")
        
        pc = Pinecone(
            api_key=PINECONE_API_KEY
        )

        # Now do stuff
        if 'influencer-marketing-brief' not in pc.list_indexes().names():
            pc.create_index(
                name='influencer-marketing-brief', 
                dimension=1536, 
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
        index = pc.Index("influencer-marketing-brief")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size = 1000,
            chunk_overlap = 200,
        )

        chunks = splitter.split_text(text)

        for i,chunk in enumerate(chunks):
            print(f"Chunk {i+1}: {chunk[:100]}...")  # Print first 100 characters of each chunk
            response = openai_client.embeddings.create(
                input = [chunk],
                model = "text-embedding-ada-002"
            )
            vec = response.data[0].embedding
            meta = {"text": chunk,"client_id":client_id}
            index.upsert(vectors=[(f"{client_id}_{i+1}", vec, meta)])  # Using chunk index as ID

        print("Document indexed successfully.")
        return index
    
    except Exception as e:
        print(f"Error processing documents: {e}")
        return False


def generate_sql_from_influencer_brief(index, client_id):
    try:
        # 5. User query example
        user_query = """ Create a vector database query to retrieve embedding for this criteria:
                        
                        Find the Ideal Influencer criteria in the influencer brief.
                        Looking for these details:
                        1. Target Audience
                        2. Influencer Followers Count
                        3. Influencer Nationality
                        4. Influencer Region
                        5. Targeted Domain
        """

        # Embed query and retrieve context
        q_res = openai_client.embeddings.create(input=[user_query], model="text-embedding-ada-002")
        q_vec = q_res.data[0].embedding

        query_resp = index.query(
            vector=q_vec,
            top_k=5,
            filter={"client_id":client_id},  # restrict to this client's criteria
            include_metadata=True
        )

        retrieved_texts = [match['metadata']['text'] for match in query_resp['matches']]
        print(f"Retrieved {len(retrieved_texts)} relevant chunks for the query.")
        query_context = " ".join(retrieved_texts)

        # 6. Generate SQL via GPT (schema must be included)
        schema = """
        Database schema with column descriptions:
                Table: src_influencer_data (
                id                          character varying(100000) -- Unique identifier for the influencer
                instagram_url               character varying(100000) -- URL of the influencer's Instagram profile
                instagram_followers_count   character varying(100000) -- Number of followers on Instagram
                instagram_username          character varying(100000) -- Instagram username/handle
                instagram_bio               character varying(100000) -- Bio text from the Instagram profile
                influencer_type             character varying(100000) -- Type/category of influencer (fixed category values among this: [food_vlogger,fashion_vlogger,real_estate_influencers,business_vloggers,finance_vloggers,real_estate_influencers,beauty_vlogger,tech_vloggers])
                influencer_location         character varying(100000) -- Location of the influencer
                instagram_post_urls         character varying(100000) -- List of URLs to the influencer's Instagram posts
                business_category_name      character varying(100000) -- Main business category of the influencer (Tag provided by Instagram for Business profile Eg: "Personal blog","Digital creator","Reel creator" etc)
                full_name                   character varying(100000) -- Full name of the influencer
                instagram_follows_count     character varying(100000) -- Number of accounts the influencer follows
                created_time                character varying(100000) -- Timestamp when the influencer was added to the database
                instagram_hashtags          character varying(100000) -- Hashtags used by the influencer for different posts (stored as list of strings)
                instagram_captions          character varying(100000) -- Captions from the influencer's posts (stored as list of strings)
                instagram_video_play_counts character varying(100000) -- Number of plays for video posts (stored as list of strings)
                instagram_likes_counts      character varying(100000) -- Number of likes on posts (stored as list of strings)
                instagram_comments_counts   character varying(100000) -- Number of comments on posts (stored as list of strings)
                instagram_video_urls        character varying(100000) -- URLs of video posts
                instagram_posts_count       character varying(100000) -- Total number of posts by the influencer
                external_urls               character varying(100000) -- List of external links provided by the influencer
                instagram_profile_pic       character varying(100000) -- URL of the influencer's profile picture
                influencer_nationality      character varying(100000) -- Nationality of the influencer (Include country names)
                targeted_audience           character varying(100000) -- Target audience group for the influencer (fixed category values among this: ["gen-z","gen-y", "gen-x"])
                targeted_domain             character varying(100000) -- Domain or industry targeted by the influencer (fixed categoru values among this: ["food", "fashion", "fitness", "gaming", "education", "automotive", "finance", "art"])
                profile_type                character varying(100000) -- Type of profile (fixed category values among this: ["person","group"])
                email_id                    character varying(100000) -- Email address of the influencer (if not available value is "NA")
                twitter_url                 character varying(100000) -- URL of the influencer's Twitter profile
                snapchat_url                character varying(100000) -- URL of the influencer's Snapchat profile
                phone                       character varying(100000) -- Phone number of the influencer ( if not available value is "NA")
                linkedin_url                character varying(100000) -- URL of the influencer's LinkedIn profile
                tiktok_url                  character varying(100000) -- URL of the influencer's TikTok profile
                )
        """

        # Construct the prompt
        user_prompt = f"""
        {schema}
        Influencer Criteria required for the brand to query relevant influencers: {query_context}
        SQL:
        """

        system_prompt = """
        You are a helpful assistant that converts natural language into SQL queries.
        You must always generate an SQL query on the table `src_influencer_data`.

        - In the SELECT clause, always use `SELECT *` to return all columns from the table.

        - In the WHERE clause or other conditions, you are allowed to use any columns from the table (e.g., instagram_bio, instagram_hashtags, etc.)

        - Always limit the result to a maximum of 3 records using `LIMIT 3`.

        - Do not return explanations, markdown, or SQL tags like ```sql.

        Example (one liner ready to use SQL query):
        SELECT * FROM src_influencer_data WHERE instagram_followers_count::int > 10000 LIMIT 3;
        """

        # Call the OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        sql_query = response.choices[0].message.content

        # Add LIMIT 3 if it's not already present
        if "limit" not in sql_query.lower():
            if ";" in sql_query:
                sql_query = sql_query.rstrip(";") + " LIMIT 3;"
            else:
                sql_query += " LIMIT 3;"

        print("Generated SQL Query:")
        # print(sql_query)
        sql_query = sql_query.replace("\n", " ")
        # print(sql_query)
        return sql_query
    
    except Exception as e:
        print(f"Error generating SQL from influencer brief: {e}")
        return None


def influencer_brief_processing(drive_urls_str, client_id):
    """
    Process the influencer brief documents and generate SQL query.
    :param files: List of file paths to process.
    :param client_id: Client ID for which the documents are processed.
    :return: SQL query string or None if processing fails.
    """
    drive_urls = ast.literal_eval(drive_urls_str)  # Converts JSON string → Python list
    files = []
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    print(f"SCRIPT_DIR: {SCRIPT_DIR}")
    for i,drive_url in enumerate(drive_urls):
        folder_path = f"drive_uploads/demo_{i+1}.docx"
        output_path = os.path.join(SCRIPT_DIR, folder_path)
        print(f"full path: {output_path}")
        files.append(download_file_from_drive(drive_url, output_path))

    print(files)
    index = process_documents(files, client_id)
    if index:
        sql_query = generate_sql_from_influencer_brief(index, client_id)
        if sql_query:
            print("SQL Query generated successfully.")
            print(sql_query)
        else:
            print("Failed to generate SQL query.")
    else:
        print("Failed to process documents.")
    return sql_query

if __name__ == "__main__":
    # Example usage
    drive_urls_str = """["https://drive.google.com/uc?id=1IoCxHQP8dKBgrGLjeUcDq75Y9Ip97dVf&export=download"]"""
    client_id = "aarka"
    sql_query = influencer_brief_processing(drive_urls_str, client_id)
    
  