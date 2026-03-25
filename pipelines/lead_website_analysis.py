import os
import openai
from error_logger import execute_error_block
from datetime import datetime, timezone
from db.db_utils import update_client_vector,fetch_client_column
import json
from langchain_community.embeddings import OpenAIEmbeddings
from apify_client import ApifyClient
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

CLIENT_DETAILS_TABLE_NAME = os.getenv("CLIENT_DETAILS_TABLE_NAME")
CLIENT_CONFIG_TABLE_NAME = os.getenv("CLIENT_CONFIG_TABLE_NAME")

def get_client_value_proposition(tokenizer,index):
  try:
    print(f"----------Started Client Value Proposition Analysis ----------")
    value_proposition_query_v2 = """
    Provide a detailed overview of the company based on the extracted content. 
    Include the following aspects explicitly if mentioned: 
    - The company's full name and industry.  
    - A brief company history and major milestones.  
    - Core offerings, products, or services.  
    - Target audience or industries served.  
    - Unique value propositions or differentiating factors.  
    - Major clients, partnerships, and collaborations.  
    - Key financials (if available), such as revenue, market position, or growth metrics.  
    - Any other notable details that define the company's market presence.  
    Ensure the response is **strictly based on extracted content** without assumptions.
    """

    # Increase retrieval depth and improve relevance
    retriever = index.vectorstore.as_retriever(search_kwargs={"k": 30})  # Increased `k`
    retrieved_docs = retriever.invoke(value_proposition_query_v2)

    # Filter out empty or irrelevant documents
    filtered_docs = [doc for doc in retrieved_docs if len(doc.page_content.strip()) > 50]  # Adjust threshold as needed

    # Extract text from the top-ranked relevant documents
    retrieved_texts = [doc.page_content for doc in filtered_docs]
    sources = [doc.metadata.get("source", "Unknown") for doc in filtered_docs]

    # Print Retrieved Document Count
    print(f"Retrieved {len(filtered_docs)} relevant documents.")

    context = "\n\n".join(retrieved_texts)
    tokenized_context = tokenizer.encode(context, truncation=True, max_length=2200)
    trimmed_context = tokenizer.decode(tokenized_context)

    client_value_proposition_prompt = f"""
    ### 🚀 Extract Verified Company Information – No Assumptions 🚀  
    You are analyzing structured company information strictly based on **verified website content**.  
    Your task is to **extract and categorize details** under the specified sections.  

    🚨 **Rules:**  
    ✅ Use **only** the information provided in the context.  
    🚫 **Do NOT infer or assume** missing details.  
    🚫 **Do NOT include generic industry knowledge.**  

    ---  
    ### **Company Overview**  
    🔹 **Company Name & Industry:** Identify the company's official name and industry.  
    🔹 **Company History & Milestones:** List achievements, partnerships, or significant events (only if explicitly mentioned).  

    ### **Unique Company Aspects**  
    🔹 **Key Offerings:** Provide a detailed list of **products, solutions, or services** mentioned. Avoid generic descriptions.  
    🔹 **Target Audience:**  
      - Identify **specific industries** the company serves (e.g., Healthcare, Finance, Retail, Manufacturing, etc.).  
      - List any **specific client names or sectors** if mentioned.  
      - If industry names are **not explicitly mentioned**, list **examples of products/services** that indicate industry focus.  
    🔹 **Differentiating Factors:** Highlight what makes the company unique (e.g., proprietary tech, partnerships).  

    ### **Competitive Positioning & Market Impact**  
    🔹 **Major Clients & Partnerships:** List major clients, collaborations, or industry partnerships (if stated).  
    🔹 **Key Statistics:** Extract **quantitative data** such as revenue, growth metrics, or market share (if available).  

    ---  
    📌 **Extracted Website Content:**  
    {trimmed_context}  

    📌 **Structured Response:**  
    """

    llm = OpenAI(temperature=0, max_tokens=1500)  # Increased output space
    client_value_proposition = llm.invoke(client_value_proposition_prompt)
    
    print("\nClient Value Proposition:", client_value_proposition)
    print("\nSources:", sources)
    return client_value_proposition

  except Exception as e:
    execute_error_block(f"Error occured while getting client value proposition, {e}")

def get_icp(tokenizer,index):
  try:
      print("================ Analyzing Ideal Customer Profile ======================\n\n")
      content_extraction_query = """
      Retrieve and extract all available information to determine the Ideal Customer Profile (ICP) of the company. 
      Focus only on explicitly mentioned data and avoid assumptions.

      ### **What to Extract?**  
      1️⃣ **Industries & Business Types Served:** Look for direct mentions of industry names, business categories, or sectors.  
      2️⃣ **Customer Segments:** Identify key client groups (e.g., startups, enterprises, government, e-commerce).  
      3️⃣ **Geographical Focus:** Extract locations where the company operates or provides services.  
      4️⃣ **Case Studies & Testimonials:** Identify customer success stories, mentions of previous clients, or reference businesses.  
      5️⃣ **Pain Points Solved:** Identify challenges the company addresses for its clients (if explicitly stated).  

      📌 **Extraction Scope:** Use content from the "About Us," "Products/Services," "Case Studies," "Testimonials," and blog sections if available.  
      📌 **Strictly No Assumptions:** Only use details explicitly mentioned in the dataset.  

      Return all extracted information in a structured format.  
      """

      # Increase retrieval depth and improve relevance
      retriever = index.vectorstore.as_retriever(search_kwargs={"k": 30})  # Increased `k`
      retrieved_docs = retriever.invoke(content_extraction_query)

      # Filter out empty or irrelevant documents
      filtered_docs = [doc for doc in retrieved_docs if len(doc.page_content.strip()) > 50]  # Adjust threshold as needed

      # Extract text from the top-ranked relevant documents
      retrieved_texts = [doc.page_content for doc in filtered_docs]
      sources = [doc.metadata.get("source", "Unknown") for doc in filtered_docs]

      # Print Retrieved Document Count
      print(f"Retrieved {len(filtered_docs)} relevant documents.")

      # Join retrieved content
      context = "\n\n".join(retrieved_texts)

      # Truncate the input dynamically
      tokenized_context = tokenizer.encode(context, truncation=True, max_length=1500)
      trimmed_context = tokenizer.decode(tokenized_context)
      # print(trimmed_context)

      explicit_icp_criteria = "Not available"
      prompt_expanded = f"""
      ### Task: Extract Ideal Customer Profile (ICP) from Website Content

          #### **🔍 Objective**
          Analyze the **company's website** to extract its **Ideal Customer Profile (ICP)** based on **industry, market positioning, and offerings**.  
          The ICP will help retrieve **high-value prospects** from **Apollo.io** for **targeted outreach**.  

          ---

          #### **🚨 STRICT Criteria**  
          ✔ **Primary Source:** Extract ICP attributes **strictly from website content**.  
          ✔ **Explicit Criteria:** If provided (`{explicit_icp_criteria}`), prioritize it **alongside** website insights.  
          ✔ **If `{explicit_icp_criteria}` = `"Not available"`, rely entirely on website content**.  
          ✔ **STRICTLY exclude irrelevant profiles.**  

          ---

          #### **📌 ICP Attributes to Extract**  

          ##### **1️⃣ Job Titles (Minimum 5 - STRICT, No Invalid Responses)**  
          🔴 **IMPORTANT**:  
          - **ALWAYS return at least 5 job titles**.  
          - If fewer than 5 job titles exist, **infer closely related job titles** from context instead of returning fewer than 5.  
          - If no exact matches are available, **derive general industry-relevant job titles**.  

          ##### **2️⃣ Seniority Levels (Minimum 4 - STRICT, Unique Values Required)**  
          🔴 **IMPORTANT**:  
          - Extract at least **4 unique seniority levels**.  
          - **DO NOT repeat the same seniority level** (e.g., avoid `["Senior", "Senior", "Senior", "Senior"]`).  
          - If limited seniority data is available, **infer additional relevant seniority levels**.  

          ##### **3️⃣ Geographic Targeting (At Least 1, Can Be More - Unique Countries Required)**  
          🔴 **IMPORTANT**:  
          - Extract **at least 1 country**, but **include multiple if available**.  
          - Ensure extracted locations are **strictly countries** (e.g., avoid cities or regions like `"Dubai"`, use `"United Arab Emirates"`).  
          - If the company’s client locations are not explicitly mentioned, **extract the company's location and include nearby countries**.  

          ##### **4️⃣ Ideal Company Size - Minimum 3 Ranges (STRICT)**  
          - **Extract at least 3 distinct company size tags** (e.g., `'1,10'`, `'11,50'`, `'51,200'`).  

          ---

          #### **✅ Extraction Guidelines**  
          ✔ **Website content is the primary source.**  
          ✔ If `{explicit_icp_criteria}` is available, **merge it with extracted insights**.  
          ✔ STRICTLY **ensure minimum counts for each category.**  
          ✔ **NEVER return "INVALID" or an empty list—always generate the closest possible matches**.  
          ✔ **Ensure diversity in extracted values (no duplicates within lists).**  

          ---

          #### **🚀 JSON-ONLY Output**  
          ⚠️ **Return ONLY a JSON object** with unique values in each category—DO NOT include explanations.  

          ```json
          {{
            "job_titles": ["<job_title_1>", "<job_title_2>", "<job_title_3>", "<job_title_4>", "<job_title_5>", ...],
            "person_seniorities": ["<unique_seniority_1>", "<unique_seniority_2>", "<unique_seniority_3>", "<unique_seniority_4>", ...],
            "person_locations": ["<unique_location_1>", "<unique_location_2>", "<unique_location_3>", ...],
            "employee_range": ["<size_1>", "<size_2>", "<size_3>", ...]
          }}
      ---  
      📌 **Extracted Website Content:**  
      {trimmed_context}  

      📌 **Structured Response:**  
      """
      
      llm = OpenAI(temperature=0, max_tokens=1500)  # Increased output space

      icp_tags = llm.invoke(prompt_expanded)
      print("\n🚀 ICP tags:\n", icp_tags)
      print("\n📌 Sources:", sources)

      icp_analysis_prompt = f"""
          Analyze the **company's website content** to extract its **Ideal Customer Profile (ICP)** based on **industry, market positioning, and offerings**.  
          The ICP will help retrieve **high-value prospects** from **Apollo.io** for **targeted outreach**.  
          company's website content: {trimmed_context}
          The ouptut should be short and precise and STRICTLY in English language
      """
      llm = OpenAI(temperature=0, max_tokens=1500)  # Increased output space

      icp_analysis = llm.invoke(icp_analysis_prompt)
      print("\n🚀 ICP analysis:\n", icp_analysis)
      print("\n📌 Sources:", sources)
      return icp_tags,icp_analysis

  except Exception as e:
    execute_error_block(f"Error occured while fetching the ICP. {e}")

def get_apollo_tags(icp_information):
  try:
    updated_json_prompt = f"""
        From the information gathered regarding the Ideal Customer Profile of the company: {icp_information}, segregate the details into different sections:
        1. job_titles
        2. person_seniorities
        3. person_locations
        4. employee_range

        Strictly pick values **only from the given lists** below. Do not generate or infer any values outside these lists.

        **Job Titles** (Select at least 5, only from this list):
        job_titles = [
            "ceo",
            "coo",
            "cto",
            "cmo",
            "cio",
            "cfo",
            "e-commerce specialist",
            "vp of sales",
            "marketing manager",
            "marketing coordinator",
            "digital marketing manager",
            "director of marketing",
            "director of sales",
            "business development managers",
            "sales associate",
            "vp of marketing",
            "vp of engineering",
            "director of product management",
            "director of operations",
            "director of hr",
            "director of engineering",
            "sales manager",
            "product manager",
            "operations manager",
            "branding manager",
            "hr manager",
            "it manager",
            "customer success manager",
            "data scientist",
            "product designer",
            "marketing specialist",
            "sales representative",
            "business analyst",
            "customer support specialist",
            "marketing assistant",
            "sales associate",
            "hr coordinator",
            "business development managers",
            "administrative assistant",
            "freelancer",
            "contractor",
            "growth hacker",
            "scrum master",
            "social media strategist",
            "content creator"
        ]

        **Person Seniorities** (Only select from this list):
        person_seniorities = [
            "owner",
            "founder",
            "c_suite",
            "partner",
            "vp",
            "head",
            "director",
            "manager",
            "senior",
            "entry",
            "intern"
        ]

        **Person Locations** (Minimum 1 required, only from this list):
        person_locations = [
            "Dubai",
            "UAE",
            "United Arab Emirates",
            "Abu Dhabi",
            "Sharjah",
            "Ajman",
            "Riyadh",
            "Manama",
            "Bahrain",
            "Muscat",
            "Kuwait",
            "Jordan",
            "Lebanon",
            "Qatar",
            "Oman",
            "Saudi Arabia",
            "Australia",
            "France",
            "South Africa",
            "India",
            "China",
            "United States",
            "Russia",
            "Germany",
            "Italy",
            "Canada",
            "United Kingdom"
        ]

        **Employee Range** (Select only the available options as it is from this list):
        employee_range = [
            "1,100",
            "1,500",
            "500,10000",
            "50,1000",
            "1,1000",
            "1,50",
            "11,50",
            "51,200",
            "201,500",
            "501,1000",
            "1000,5000",
            "5001,10000"
        ]

        ### 🚀 Expected Response Format (Return JSON String)  
        - Return **ONLY** a JSON string. No explanations, no additional text, no extra formatting.  
        - **The output must be directly usable as a string literal in Python.**  

        **Example Output Format:**  

        {{"job_titles": ["Marketing Manager", "Head of Growth", "Digital Strategist"],
        "person_seniorities": ["Mid-Level", "Senior", "Director", "VP"],
        "person_locations": ["United States", "Canada", "UK"],
        "employee_range": ["11-50", "51-200", "201-500"]}}

        **If no relevant data is found, return:**  

        {{"job_titles": [], "person_seniorities": [], "person_locations": [], "employee_range": []}}  
    
    """

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
      model="gpt-4",
      messages=[{"role": "user", "content": updated_json_prompt}]
    )
    # print(response.choices[0].message.content)
    result = response.choices[0].message.content
    return result
  except Exception as e:
   execute_error_block(f"Error occured while creating apollo tags: {e}") 

def analyze_website(website_url,explicit_icp_criteria="Not available"):
  try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    print(" Started Website Analysis")
    print("\n--------------------------------------------------------\n")
    print("Initiating the Apify Actor run...")

    loader = apify.call_actor(
        actor_id="apify/website-content-crawler",
        run_input={"startUrls": [{"url": website_url}], "maxCrawlPages": 20},
        dataset_mapping_function=lambda item: Document(
            page_content=item["text"] or "", metadata={"source": item["url"]}
        ),
        timeout_secs=140
    )

    time_stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d-%H-%M-%S')
    print(f"Time : {time_stamp}")
    chroma_folder = f"chroma_data_{website_url.replace('https://', '').replace('/', '_')}_{time_stamp}"
    print(f"Chroma folder name: {chroma_folder}")
    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    print(f"Dataset id of the loader : {loader.dataset_id}") # Gives datasetid of the loader
    
    # Step 1: Define Embeddings & Vector Store Index
    embedding_function = OpenAIEmbeddings()

    print(f"Fetching vector  store index")
    # Now use sqlite3 as usual
    import sqlite3
    print(f"Sqlite3 version : {sqlite3.sqlite_version}")  
    index = VectorstoreIndexCreator(
        vectorstore_cls=Chroma,  
        embedding=embedding_function,  
        vectorstore_kwargs={"persist_directory": chroma_folder}  
    ).from_loaders([loader])  
    print(f"Started website analysis...")
    icp_tags,icp_analysis = get_icp(tokenizer,index)
    retries = 5
    while retries > 0:
      apollo_tags = get_apollo_tags(icp_tags)
      try:
        json.loads(apollo_tags)
        print(f"The apollo tags are now in JSON format")
        break
      except ValueError:
        retries -= 1
        print(f"Retrying the JSON tags creation...")

    client_value_proposition = get_client_value_proposition(tokenizer,index)
    print(f"Apollo tags: {apollo_tags}")

    print("================Completed Web analysis======================\n\n")

    print("\n--------------------------------------------------------\n")
    icp_details = icp_analysis + "\n\n" + icp_tags
    return icp_details,apollo_tags,client_value_proposition
  
  except Exception as e:
    print(f"Error occured while analyzing the website : {e}")

def get_website_content(website_url):
  try:
    # Run the Website Content Crawler on a website, wait for it to finish, and save its results into a LangChain document loader:
    loader = apify.call_actor(
        actor_id="apify/website-content-crawler",
        run_input={"startUrls": [{"url": website_url}], "maxCrawlPages": 30},
        dataset_mapping_function=lambda item: Document(
            page_content=item["text"] or "", metadata={"source": item["url"]}
        ),
    )
    return loader

  except Exception as e:
    execute_error_block(f"Exception occured while analyzing the website content : {e}")

def query_web_content(loader,query):
  try:
    # Initialize the vector database with the text documents:
    index = VectorstoreIndexCreator(embedding=OpenAIEmbeddings()).from_loaders([loader])

    result = index.query_with_sources(query, llm=OpenAI())

    print("answer:", result["answer"])
    print("source:", result["sources"])
    return {"answer":result["answer"],"source":result["sources"]}
  
  except Exception as e:
    execute_error_block(f"Exception occured while querying web content: {e}")

def chroma_db_testing():
    try:
        # Replace sqlite3 with pysqlite3
        __import__('pysqlite3')
        import sys
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

        # Now use sqlite3 as usual
        import sqlite3
        print(sqlite3.sqlite_version)  

        return True
    except Exception as e:
        print(f"Error occured while testing chromadb")
        return False
    
def scrape_website(website_url):
  try: 
    print("Started Website Scraping using Apify...")
    apify_api_key = os.getenv("APIFY_API_TOKEN")
    apify_client = ApifyClient(apify_api_key)
    result = apify_client.actor("apify/website-content-crawler").call(
    run_input={"startUrls": [{"url": website_url}], "maxCrawlPages": 50},
    timeout_secs=600
    )
    # How to get the items stored inside the Apify result
    dataset_id = result["defaultDatasetId"]
    dataset = apify_client.dataset(dataset_id)
    list_page = dataset.list_items()  # Get the ListPage object
    items = list_page.items  # Access the 'items' attribute directly
    documents = [
    Document(page_content=item.get("text", ""), metadata={"source": item["url"]})
    for item in items
    ]
    print(f"Number of webpages scraped: {len(documents)}")
    return documents
  
  except Exception as e:
    execute_error_block(f"Exception occured while scraping the website: {e}")

def retrieve_info(vector_store):
  try:
    icp_prompt = """
      You are retrieving an **Ideal Customer Profile (ICP)** using stored website content from a **vector database**.  

      Analyze the extracted website content to determine the Ideal Customer Profile (ICP) for the company. Your task is to think critically and make informed decisions based on the company’s business context, offerings, and target audience.

      ### Instructions:
      - Use only explicit website content for primary extraction.
      - Make intelligent inferences where data is missing, ensuring logical consistency.
      - Identify patterns, key phrases, and industry context to construct a meaningful ICP.
      - Strictly return structured JSON String output based on the extracted attributes.

      ---  

      ### **ICP Attributes to Extract:**  

      1️⃣ **Job Titles** *(Min: 5 Relevant Titles, No Invalid Responses)*  
      - Extract key decision-making roles that would be the most relevant customers for this business.
      - If fewer than 5 are explicitly stated, infer logically based on the industry.  

      2️⃣ **Seniority Levels** *(Min: 4 Unique Levels, No Duplicates)*
      - Identify the typical seniority of decision-makers.
      - Avoid redundancy and ensure seniority is industry-appropriate.  
      - Extract **at least 4 unique seniority levels**.  

      3️⃣ **Geographic Targeting** *(Min: 1 Country, More If Available)*  
      - Identify the company’s target locations.
      - Extract countries explicitly mentioned or derive based on the company's own presence.
      - Do NOT use cities; always extract countries or regions.

      4️⃣ **Ideal Company Size** *(Min: 3 Size Ranges)*  
      - Identify the ideal company size that would benefit most from this business’s offerings.
      - If not explicitly mentioned, derive from context (e.g., if it serves enterprises, extract relevant company size ranges).

      ---  

      ### **Output Format -  JSON Text Only (No Explanations, No Extra Text)**  

      If data exists:  
      "{
        "job_titles": [job_title_1, job_title_2, job_title_3],
        "person_seniorities": [person_seniority_1, person_seniority_2, person_seniority_3, person_seniority_4],
        "person_locations": [person_location_1, person_location_2],
        "employee_range": [employee_range_1, employee_range_2, employee_range_3]
      }"

      If **no relevant data**, return:  
      "{"job_titles": [], "person_seniorities": [], "person_locations": [], "employee_range": []}"
      The output sure be pure JSON text without "json" before it
    """
    query = icp_prompt
    llm = ChatOpenAI(
        model = "gpt-4o",
        temperature = 0
    )
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever()
    )
    output = qa.invoke(query)    
    return output['result']

  except Exception as e:
    execute_error_block(f"Exception occured while retrieving info from the vector db: {e}")

def web_analysis(website_url,config_type,client_id):
  try:
    # icp_flag = fetch_client_column(CLIENT_CONFIG_TABLE_NAME,client_id,"icp_flag")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_env = os.getenv("PINECONE_ENVIORONMENT")
    index_name = client_id
    documents = scrape_website(website_url)
    text_splitter = RecursiveCharacterTextSplitter()
    split_docs = text_splitter.split_documents(documents)
    client = Pinecone(api_key=pinecone_api_key, environment=pinecone_env)
    index_name = index_name.replace("_", "-")
    update_client_vector(CLIENT_CONFIG_TABLE_NAME,client_id,index_name)
    indexes = client.list_indexes().names()
    if index_name in indexes:
      print(f"Deleting the existing index")
      client.delete_index(index_name)
    print(f"Creating index")
    client.create_index(
        name=index_name,
        dimension=1536,  
        metric="cosine",  
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    print(f"getting embeddings")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    print(f"Creating vector store")
    vector_store = PineconeVectorStore.from_documents(split_docs,embeddings,index_name=index_name)
    print('Created vector store')
    print(f"retrieving info")
    retries = 7
    print(f"Config type: {config_type}")
    if str(config_type).upper() != "CUSTOM":
      apollo_tags = {"job_titles": [], "person_seniorities": ["owner","founder","c_suite","partner","vp","head","director","manager","senior"], "person_locations": [], "employee_range": []}
      # while retries > 0:
      #   icp_tags = retrieve_info(vector_store)
      #   try:
      #     print(f"Apollo tags: {icp_tags}\n")
      #     apollo_tags = json.loads(icp_tags)
      #     print(f"The apollo tags are now in JSON format")
      #     break
      #   except ValueError:
      #     retries -= 1
      #     print(f"Retrying the JSON tags creation...")
      #     if retries ==0:
      #       execute_error_block(f"Error occured during Apollo tag creation, the string is not in proper JSON.")
    else:
        apollo_tags = {"job_titles": [], "person_seniorities": ["owner","founder","c_suite","partner","vp","head","director","manager","senior"], "person_locations": [], "employee_range": []}
    print(f"Apollo tags: {apollo_tags}")
    print(f"Successfuly generated Apollo tags")
    return index_name,apollo_tags
  
  except Exception as e:
    execute_error_block(f"Exception occured in {__name__} while running the web analysis function: {e}")

if __name__ == "__main__":
  website_url = "https://www.tmeworldwide.com/"
  analyze_website(website_url)
  


