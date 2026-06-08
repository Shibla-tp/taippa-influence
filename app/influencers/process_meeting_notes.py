import pandas as pd
from docx import Document
import pdfplumber
import openai,pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec
from PIL import Image
import pytesseract
import os
import ast
import requests
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,PINECONE_API_KEY

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
def populate_meeting_notes(data,client_id):
    try:

        print(f"Creating Pinecone index and embedding the document...")
        
        pc = Pinecone(
            api_key=PINECONE_API_KEY
        )

        # Now do stuff
        if 'influencer-marketing' not in pc.list_indexes().names():
            pc.create_index(
                name='influencer-marketing', 
                dimension=1536, 
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
        index = pc.Index("influencer-marketing")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size = 1000,
            chunk_overlap = 200,
        )

        chunks = splitter.split_text(data)

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
        return ""