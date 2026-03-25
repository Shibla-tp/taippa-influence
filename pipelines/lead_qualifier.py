import openai
from error_logger import execute_error_block
from db.db_utils import export_to_airtable
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS
from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

def qualify_lead(apollo_id,lead_details,index_name):
    try:
        title = lead_details['title']
        seniority = lead_details['seniority']
        headline = lead_details['headline']
        employment_summary = lead_details['employment_summary']
        
        print(f"Title: {title}, headline: {headline}, seniority: {seniority}, employment_summary: {employment_summary}")
        
        qualification_prompt = f"""
        Your task is to qualify a given person as a 'warm lead' based on the company information available in the vector. 
        The main intent is to filter out only those who have a **good probability** of responding to a **personalized cold email** 
        or visiting the website linked in our email.

        ### Lead Qualification Criteria:
        A **warm lead** is defined as:
        ✅ Someone who has the potential to show interest in our product or service.
        ✅ Someone to whom we can send a high-performing personalized cold email.
        ✅ Someone who has a **slight probability** of responding or visiting our website.

        ### Person’s Details:
        - **Title:** {title}
        - **Job Seniority:** {seniority}
        - **LinkedIn Profile Headline:** {headline}
        - **Employment Summary:** {employment_summary}     

        ### Your Task:
        1. **Analyze the relevance** of the person's role, seniority, and background to our value proposition.
        2. **Generalize based on available details** rather than overfitting to specific data points.
        3. **Determine their likelihood** of being a warm lead by evaluating how well they align with our product/service.
        4. **Final Decision:**
          - Respond with **Yes** if the person is a warm lead and provide a brief justification.
          - Respond with **No** if the person is unlikely to engage, along with a short explanation.

        """
        """  ### Response Format:
        ✅ **Yes** – This person is a warm lead because they work in [relevant industry], hold a decision-making position, and have experience in [related functions]. They are likely to find our offering useful.

        ❌ **No** – This person is not a warm lead because they work in an unrelated field, do not have decision-making power, or their role does not align with our value proposition."""

        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = PineconeVectorStore(index_name=index_name,embedding=embeddings)
        retriever = vector_store.as_retriever()
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        # Setup RetrievalQA chain
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",  # Default simple retrieval method
            retriever=retriever
        )

        query = qualification_prompt
        output = qa.invoke(query)
        qualification_response = output['result']
        print('===============================================\n')
        print(f"Qualification status : {qualification_response}")
        print('===============================================\n')
        qualification_status=qualification_response[:12]
        if 'YES' in qualification_status.upper():
            status = True
        else:
            status = False
        data = {"apollo_id":apollo_id, "title": title, "headline": headline, "seniority": seniority, "employment_summary": employment_summary,"qualification_response":qualification_response,"qualification_status":str(status)}
        export_to_airtable(data,"lead_qualification_status")
        return status
    except Exception as e:  
        print(f"Error occured in {__name__} while qualifying the lead. {e}")
        return False


def qualify_lead_v1(persona_details,solution_benefits,unique_features,solution_impact_examples,domain,buyer_criteria,buyer_examples):
    try:
        title = persona_details['title']
        headline = persona_details['headline']
        country = persona_details['country']
        city = persona_details['city']
        departments = persona_details['departments']
        subdepartments = persona_details['subdepartments']
        functions = persona_details['functions']
        employment_summary = persona_details['employment_summary']

        lead_prompt = f"""
        Given the following details about a person:
        - Title: {title}
        - Headline: {headline}
        - Country: {country}
        - City: {city}
        - Departments: {departments}
        - Subdepartments: {subdepartments}
        - Functions: {functions}
        - Employment Summary: {employment_summary}

        Here is information about our company and the product we offer:
        - Solution benefits: {solution_benefits}
        - Unique features: {unique_features}
        - Solution impact: {solution_impact_examples}
        - Domain: {domain}
        - Targeted buyer criteria: {buyer_criteria}

        Below are examples of warm lead profiles. These are generic examples, which means this is not exactly how they should look:
        {buyer_examples}

        If no examples are provided, you can use the already existing information

        Now, based on the provided details, does this person match the profile of a 'warm' lead for our company?
        Answer with **Yes/No** and provide a brief justification.
        """

        # Send the request to OpenAI GPT-4
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": lead_prompt}
            ],
            max_tokens=300
        )
        # Print the response
        qualification_response = response['choices'][0]['message']['content']
        print('===============================================\n')
        print(f"Qualification status : {qualification_response}")
        print('===============================================\n')
        qualification_status=qualification_response[:5]
        return True if 'YES' in qualification_status.upper() else False
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while qualifying the lead. {e}")

def qualify_lead_test(persona_details, solution_benefits, unique_features, 
                      solution_impact_examples, domain, buyer_criteria, buyer_examples):
    try:
        title = persona_details['title']
        headline = persona_details['headline']
        country = persona_details['country']
        city = persona_details['city']
        departments = persona_details['departments']
        subdepartments = persona_details['subdepartments']
        functions = persona_details['functions']
        employment_summary = persona_details['employment_summary']
        
        lead_prompt = f"""
            Step 1:
            Please provide the average salary of a {title} in {city} with {city} currency per month. 
            Just provide the salary amount, without any justification or additional information. 
            The output should look like this: 18000

            Step 2:
            Please format the output from Step 1 as: 
            "Salary is (output from Step 1)"
            Only output this formatted statement, nothing else.
        """
        print(lead_prompt)
        # lead_prompt = """
        #     Please provide the average salary of a Data Engineer in Dubai with Dubai currency per month, 
        #     Just provide the average salary dont give justification
        #     output should look like this: average_salary: 18000 AED per month. 
        # """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": lead_prompt}
            ]
        )
        # Print the response
        qualification_response = response['choices'][0]['message']['content']
        print('===============================================\n')
        print(f"HNWI Qualification status : {qualification_response}")
        print('===============================================\n')
        return True
    
    except Exception as e:
        execute_error_block(f"Error occurred in {__name__} while running the test qualification for the lead. {e}")