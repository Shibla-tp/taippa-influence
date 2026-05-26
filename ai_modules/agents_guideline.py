import openai
# from openai import OpenAI
import requests
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,PERPLEXITY_API_KEY,PINECONE_API_KEY,PINECONE_ENVIRONMENT,ANTHROPIC_API_KEY
import pinecone
from openai import OpenAI
import json
from pinecone import Pinecone
import anthropic
from config import OPENAI_API_KEY
client = openai.OpenAI(api_key=OPENAI_API_KEY)
openai.api_key = OPENAI_API_KEY

class GuidelineGenerate:
    def __init__(self):
        self.lead_info = {}
        self.industry_type = ""
        self.person_research_data = ""
        self.company_research_data = ""
        self.company_competitors = ""
        self.pain_points = ""
        self.cvp = ""
        self.b2b_sales_content = {}
        self.linkedin_message_content = {}
        self.follow_up_email_content = {}
        self.follow_up_linkedin_message_content = {}
        self.linkedin_connection_message_content = {}
        self.linkedin_connection_message = {}
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


    def classify_company_vertical(self):
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at classifying companies into business verticals. "
                                "Respond only with one of the following tags: advertising_agencies, media_companies, or brands. "
                                "If the company is not clearly an advertising_agency or a media_company, respond with 'brands'."
                    },
                    {
                        "role": "user",
                        "content": f"Given the following information about a lead's company:\n\n"
                                f"Industry: {self.lead_info.get('industry')}\n"
                                f"Description: {self.lead_info.get('description')}\n\n"
                                f"Classify the company into one of the following verticals based on the best fit:\n"
                                f"1) advertising_agencies\n"
                                f"2) media_companies\n"
                                f"3) brands\n\n"
                                f"Respond with only one of the tags as plain text: advertising_agencies, media_companies, or brands."
                    }
                ],
                temperature=0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error occurred while classifying company: {e}")
            raise RuntimeError(f"Error occurred while classifying company: {e}")
            # return "brands"
        
    def get_recent_achievements_person(self):
        try:
            url = "https://api.perplexity.ai/chat/completions"

            payload = {
                "temperature": 0.2,
                "top_p": 0.9,
                "return_images": False,
                "return_related_questions": False,
                "top_k": 0,
                "stream": False,
                "presence_penalty": 0,
                "frequency_penalty": 1,
                "web_search_options": {"search_context_size": "low"},
                "model": "sonar",
                "max_tokens": 2000,
                "messages": [
                    {
                        "content": (
                            "You are a professional assistant helping with lead research. "
                            "Your job is to extract recent achievements and activities of a person based on available data. "
                            "If external data (e.g. LinkedIn) is not accessible, summarize using the given employment summary and LinkedIn bio."
                        ),
                        "role": "system"
                    },
                    {
                        "role": "user",
                        "content": f"""
                                    These are some information about a prospective lead:
                                    Recipient's role: {self.lead_info.get('recipient_role')}
                                    Recipient's Name: {self.lead_info.get('recipient_first_name')} {self.lead_info.get('recipient_last_name')}
                                    Recipient's LinkedIn bio: {self.lead_info.get('recipient_bio')}
                                    Recipient's Employment Summary:
                                    {self.lead_info.get('employment_summary')}
                                    Recipient's Company Website: {self.lead_info.get('recipient_company_website')}

                                    Find information about this person through their LinkedIn.
                                    Search for {self.lead_info.get('recipient_first_name')} working at {self.lead_info.get('recipient_company')} on LinkedIn.

                                    Output:
                                    Only return the recipient's recent achievements and activities as plain text. If the information is not available, use the recipient's employment summary and LinkedIn bio. Do not include any other details or commentary.
                                    """
                    }
                ]
            }
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
            response = requests.request("POST", url, json=payload, headers=headers)
            # print(response.text)
            return response.json().get('choices')[0].get('message').get('content')
            # return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error occurred while generating summary: {e}")
            raise RuntimeError(f"Error occurred while getting recent achievements person: {e}")

    def get_recent_achievements_company(self):
        try:
            url = "https://api.perplexity.ai/chat/completions"

            payload = {
                "temperature": 0.2,
                "top_p": 0.9,
                "return_images": False,
                "return_related_questions": False,
                "top_k": 0,
                "stream": False,
                "presence_penalty": 0,
                "frequency_penalty": 1,
                "web_search_options": {"search_context_size": "low"},
                "model": "sonar",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional assistant skilled at corporate research. "
                                "Your task is to identify and summarize the latest achievements of a company based on a lead’s role and the company’s website."
                    },
                    {
                        "role": "user",
                        "content": f"These are some information about a prospective lead:\n"
                                f"Recipient's role: {self.lead_info.get('recipient_role')}\n"
                                f"Recipient's Company Website: {self.lead_info.get('recipient_company_website')}\n\n"
                                f"Find recent information related to this job role in the company associated with {self.lead_info.get('recipient_first_name')} {self.lead_info.get('recipient_last_name')}.\n\n"
                                f"Output:\n"
                                f"Please return the recipient's latest company's achievement."
                    }
                ]
            }

            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }

            response = requests.request("POST", url, json=payload, headers=headers)
            # print(response.text)
            return response.json().get('choices')[0].get('message').get('content')
            # return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error occurred while generating summary: {e}")
            raise RuntimeError(f"Error occurred while getting recent achievements company: {e}")
    
    def get_competitors_company(self):
        try:
            url = "https://api.perplexity.ai/chat/completions"
            payload = {
                "temperature": 0.2,
                "top_p": 0.9,
                "return_images": False,
                "return_related_questions": False,
                "top_k": 0,
                "stream": False,
                "presence_penalty": 0,
                "frequency_penalty": 1,
                "web_search_options": {"search_context_size": "low"},
                "model": "sonar",
                "max_tokens": 2000,
                "messages": [
                    {
                        "content": (
                            "You are a professional assistant helping with lead research to get the competitors of a company. "
                        ),
                        "role": "system"
                    },
                    {
                        "role": "user",
                        "content": f"""
                                    Provide a list of 2 close competitors for {self.lead_info.get('recipient_company')} within the following industry vertical: {self.industry_type}
                                    Output: Only return the company names as a simple comma-separated list with no explanations or extra formatting.
                                    """
                    }
                ]
            }
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
            response = requests.request("POST", url, json=payload, headers=headers)
            # print(response.text)
            return response.json().get('choices')[0].get('message').get('content')

        except Exception as e:
            print(f"Error occurred while generating summary: {e}")
            raise RuntimeError(f"Error occurred while getting competitors company: {e}")
        
    def generate_search_term_cvp_agencies(self):
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages = [
                {
                    "role": "system",
                    "content": "You are helping generate a search term for a Pinecone vector database. The goal is to find relevant information from our knowledge base that can be used to craft a value proposition marketing email. Your response must consist only of the search term, with no extra commentary or formatting."
                },
                {
                    "role": "user",
                    "content": f"""You are tasked with creating a search term for our pinecone database. This information is going to be used to create a value proposition marketing email.

                    We're targeting a {self.industry_type} who is interested ONLY in our data product.

                    This is some news about the company that might be related to the recipient:
                    {self.company_research_data}

                    Please propose a search term to search our knowledge base. Make it specific to the recipient's industry. We want to find relevant information so we can present a very specific value proposition and features they would be interested in.

                    Your response should be purely the search term with nothing else. Don't put any line breakers."""
                }
                ],
                temperature=0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error occurred while generating search term: {e}")
            raise RuntimeError(f"Error occurred while generating search term for cvp agencies: {e}")


    def generate_search_term_cvp_brands_media(self):
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are helping generate a search term for a Pinecone vector database. The goal is to find relevant information from our knowledge base that can be used to craft a value proposition marketing email. Your response must consist only of the search term, with no extra commentary or formatting."
                    },
                    {
                        "role": "user",
                        "content": f"""You are tasked with creating a search term for our pinecone database. This information is going to be used to create a value proposition marketing email.

                        We're targeting a {self.industry_type} who is interested in our data and media planning products.

                        This is some news about the company that might be related to the recipient:
                        {self.company_research_data}

                        Please propose a search term to search our knowledge base. Make it specific to the recipient's industry. We want to find relevant information so we can present a very specific value proposition and features they would be interested in.

                        Your response should be purely the search term with nothing else. Don't put any line breakers."""
                    }
                ],
                temperature=0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error occurred while generating search term: {e}")
            raise RuntimeError(f"Error occurred while generating search term for cvp brands media: {e}")

    def create_embedding_from_response_text(self,response_text):
        try:
            embedding_response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=response_text
            )
            return embedding_response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise RuntimeError(f"Error generating embedding from response text: {e}")

    def query_top_k_from_pinecone(self,query_vector, top_k=10, namespace="", include_metadata=True):
        """
        Queries the Pinecone vector database to retrieve the top-k most similar items to the provided query vector.

        Parameters:
        - query_vector (list of float): The vector representation of your query.
        - top_k (int): The number of top similar items to retrieve.
        - namespace (str): The namespace within the Pinecone index to query.
        - include_metadata (bool): Whether to include metadata in the results.

        Returns:
        - list of dict: A list of dictionaries containing the ID, score, and metadata (if included) of the top-k similar items.
        """
        try:
            pc = Pinecone(api_key=PINECONE_API_KEY)

            # Connect to the Pinecone index
            index = pc.Index("guideline-v3")

            response = index.query(
                vector=query_vector,
                top_k=10,
                include_metadata=True,  # Set to True/False based on your need
            )
            matches = response['matches']
            # print(matches)

            # Extract and return the matches
            return matches

        except Exception as e:
            print(f"An error occurred while querying Pinecone: {e}")
            raise RuntimeError(f"Error querying Pinecone: {e}")

    def generate_cvp_agencies(self, search_result_json):
        """
        Parameters:
        - recipient_company (str): Name of the recipient company.
        - company_type (str): Description of the company (e.g., 'a fintech startup').
        - company_news (str): Recent news or context about the company.
        - search_result_json (str or dict): The extracted vector search results in JSON string or dict format.

        Returns:
        - str: A paragraph highlighting the client value proposition based on the search results.
        """
        if isinstance(search_result_json, dict):
            search_result_json = json.dumps(search_result_json, indent=2)

        prompt = f"""
        You'll be given an array extracted from our vector search. Your objective is to take this array and create a paragraph that highlights the client value proposition for {self.lead_info.get('recipient_company')}

        {self.lead_info.get('recipient_company')} is a {self.get('industry_type')} who is interested in only in our data product.

        This is some news about the company that might be related to the recipient:
        {self.company_research_data}

        Write a value proposition that is specific to our client and client's industry using only the information extracted from the search result below. Do not make up information about the recipient company or our product:

        Search Result:
        {search_result_json}
        """
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2500,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text.strip()
        except Exception as e:
            print(f"An error occurred while generating the value proposition from search results: {e}")
            raise RuntimeError(f"Error generating value proposition from search results for agencies: {e}")

    def generate_cvp_brands_media(self, search_result_json):
        """
        Parameters:
        - recipient_company (str): Name of the recipient company.
        - company_type (str): Description of the company (e.g., 'a fintech startup').
        - company_news (str): Recent news or context about the company.
        - search_result_json (str or dict): The extracted vector search results in JSON string or dict format.

        Returns:
        - str: A paragraph highlighting the client value proposition based on the search results.
        """
        if isinstance(search_result_json, dict):
            search_result_json = json.dumps(search_result_json, indent=2)

        prompt = f"""
        You'll be given an array extracted from our vector search. Your objective is to take this array and create a paragraph that highlights the client value proposition for {self.lead_info.get('recipient_company')}

        {self.lead_info.get('recipient_company')} is a {self.lead_info.get('industry_type')} who is interested in only in our data product.

        This is some news about the company that might be related to the recipient:
        {self.company_research_data}

        Write a value proposition that is specific to our client and client's industry using only the information extracted from the search result below. Do not make up information about the recipient company or our product:

        Search Result:
        {search_result_json}
        """
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2500,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text.strip()
        except Exception as e:
            print(f"An error occurred while generating the value proposition from search results: {e}")
            raise RuntimeError(f"Error generating value proposition from search results for brands: {e}")

    def generate_customer_pain_point_term(self):
        """
        Generates a search term in JSON format to extract relevant pain points from the knowledge base.

        Returns:
        - dict: A dictionary containing the search term.
        """
        try:
            prompt = f"""
            You're an expert at writing marketing emails. You're tasked with writing an email to this recipient who works as {self.lead_info.get('recipient_role')} at {self.lead_info.get('recipient_company')}.

            This is some information we know about them:
            {self.person_research_data}
            {self.lead_info.get('recipient_bio')}

            This is some news about the company that might be related to the recipient:
            {self.company_research_data}

            Before writing this email, we are going to go to our knowledge base and extract relevant information that we can present to this lead.

            Based on the lead's role and industry, please propose a search term to search our knowledge base to extract pain points we can solve for them.
            Respond in plain text with no formatting or extra commentary.
            """
            
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=300,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            print(f"Retrieved response...")
            content = response.content[0].text.strip()
            print(f"content received: {content}")
            return content
        except Exception as e:
            print(f"An error occurred while generating the search term: {e}")
            raise RuntimeError(f"Error occured while generating pain point term")
            # return {"search_term": ""}
        
    def generate_pain_points(self,search_result_json) -> str:
            """
            Parameters:
            - recipient_company (str): Name of the recipient's company.
            - recipient_industry_text (str): Industry description text.
            - organization_name (str): Name of the organization.
            - company_news (str): Relevant company news content.
            - vector_search_json (str): Extracted array from vector search in JSON format.

            Returns:
            - str: A paragraph highlighting pain points.
            """
            prompt = f"""
            You'll be given an array extracted from our vector search. Your objective is to take this array and create a paragraph that highlights the major pain points for {self.lead_info.get('recipient_company')}.

            {self.lead_info.get('recipient_company')} is a {self.industry_type}.

            This is some news about the company that might be related to the recipient:
            {self.company_research_data}

            Write a paragraph that highlights the main pain points for {self.lead_info.get('recipient_company')} specific to them and their industry using only the information extracted from the search result below. Do not make up information about the recipient company or our product:

            Search Result:
            {search_result_json}
            """

            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=800,
                    temperature=0.4,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text.strip()
            except Exception as e:
                print(f"Error while generating pain points paragraph: {e}")
                raise RuntimeError(f"Error occured while generating pain points")
            
    def generate_b2b_sales_email(self):
        """
        Generates a persuasive B2B sales email for Guideline.ai targeting a specific recipient.

        Parameters:
        - recipient_first_name (str): First name of the recipient.
        - recipient_last_name (str): Last name of the recipient.
        - recipient_role (str): Role of the recipient.
        - recipient_company (str): Company where the recipient works.
        - target_industry (str): Industry of the target company.
        - competitor_company (str): Competitor company name.
        - key_pain_points (str): Key pain points in JSON format.
        - value_proposition (str): Key benefit or value proposition.

        Returns:
        - dict: A dictionary containing the structured email content.
        """
        try:
            prompt = f"""
            Generate a persuasive B2B sales email for Guideline.ai targeting {self.lead_info.get('recipient_first_name')} {self.lead_info.get('recipient_last_name')}, a {self.lead_info.get('recipient_role')} at {self.lead_info.get('recipient_company')}. 
            The email should be structured to engage the recipient, highlight key benefits, and prompt a response.

            ### Input Variables:
            - **Target company:** {self.lead_info.get('recipient_company')}
            - **Target industry:** {self.industry_type}
            - **Competitor company:** {self.company_competitors}
            - **Target role:** {self.lead_info.get('recipient_role')}
            - **Product/service:** Guideline.ai
            - **Key pain points:** {self.pain_points}
            - **Key benefit:** {self.cvp}
            ---

            ### Email Structure:

            #### 1. Subject Line:
            - References the **target company** by name
            - Creates **urgency or curiosity**
            - Hints at a **competitive advantage or efficiency gain**
            - Limited to **50-60 characters**

            #### 2. Email Body:
            - **Paragraph 1: Personalized Context (2-3 sentences)**
            - No greetings or recipient’s name.
            - Reference a **recent company announcement, initiative, or industry trend** specific to the recipient.
            - Show **research** into their current situation.
            - Identify a **challenge or opportunity** they are likely facing.

            - **Paragraph 2: Value Proposition (2-3 sentences)**
            - Introduce **Guideline.ai** as a solution to their challenge.
            - If the target industry is a brand or advertising agency, highlight insights related to **media planning and ad spend data**. If it’s a media company, focus only on **ad spend data** and omit any mention of media planning.
            - Include a **specific, quantifiable benefit** (e.g., percentages or efficiency gains).
            - Focus on **business outcomes, not features**.

            - **Paragraph 3: Social Proof (2-3 sentences)**
            - Mention a **relevant competitor or industry peer** who uses Guideline.ai.
            - Include a **specific result** they achieved.
            - Frame it as an **advantage the recipient is currently missing**.

            - **Paragraph 4: Call-to-Action (2 sentences)**
            - Request a time this week or early next week (**15-minute call**).
            - Create **slight urgency** without being pushy.

            ### Tone Guidelines

            - Professional but conversational
            - Confident without being arrogant
            - Direct without being aggressive
            - Focused on their business outcomes, not your product features
            - Slightly urgent without seeming desperate
            - Demonstrate insider knowledge of their industry

            ### OUTPUT FORMAT
            The response **must** be in **pure JSON text format** as the one given below with no additional text:

            {{
            "subject": "",
            "ice_breaker": "",
            "client_value_proposition": "",
            "case_studies": "",
            "call_to_action": ""
            }}
            """

            # client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2500,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text.strip()
            # print(f"B2B sales email content: {content}")
            return json.loads(content)

        except Exception as e:
            print(f"An error occurred while generating the sales email: {e}")
            raise RuntimeError("Error occurred while generating B2B sales email")

    def optimize_linkedin_outreach_message(self):
        """
        Optimizes LinkedIn outreach message sections based on provided information.

        Parameters:
        - ice_breaker (str): The initial engaging hook.
        - client_value_proposition (str): The value propositions of the client.
        - case_studies (str): Relevant case studies or success stories.
        - call_to_action (str): The call to action prompting a response.

        Returns:
        - dict: A dictionary containing the optimized LinkedIn message components.
        """
        try:
            prompt = f"""
            Optimize the following LinkedIn outreach message sections based on the provided information. Ensure each section is **concise, engaging, and formatted for LinkedIn** while keeping the core message intact.

            ### PROVIDED INFORMATION:
            - **Ice Breaker:** {self.b2b_sales_content.get('ice_breaker')}
            - **Client Value Propositions:** {self.b2b_sales_content.get('client_value_proposition')}
            - **Case Studies:** {self.b2b_sales_content.get('case_studies')}
            - **Call to Action:** {self.b2b_sales_content.get('call_to_action')}

            ### TASK:
            Refine and restructure the content while preserving the core message:

            1. **Ice Breaker (Engaging Hook)**
              - **Remove greetings or recipient names.**
              - Keep it **concise** while maintaining personalization and relevance.

            2. **About Company**
              - **Summarize and condense** the provided value propositions and case studies. (Client Value Proposition + Case Studies) from the details provided.
              - Highlight the **most relevant** aspects in a clear, impactful way and summarize it into one concise short section.

            3. **Call to Action (CTA)**
              - Ensure it is **direct, compelling, and encourages a response**.
              - Maintain a **conversational and professional tone**.

            4. **LinkedIn Subject**
              - Craft a **concise, curiosity-driven subject** that improves engagement.

            ### OUTPUT FORMAT
            The response **must** be in **pure string JSON format** as the one given below with no additional text:
            {{
            "ice_breaker_linkedin": "",
            "about_company_linkedin":"",
            "call_to_action_linkedin":"",
            "linkedin_subject":""
            }}

            ### KEY REQUIREMENTS:
            ✅ **Do not generate new content**—only **restructure and optimize** existing information.  
            ✅ Ensure the response is **brief, engaging, and LinkedIn-friendly**.  
            ✅ **No greetings or recipient names** should be included.  
            ✅ **Strictly return a JSON-formatted response with no additional text.**
            """

            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=3000,
                temperature=0.7,
                system="You are a helpful assistant that restructures LinkedIn content for engagement.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            content = response.content[0].text.strip()
            print(f"Linkedin content: {content}")
            return json.loads(content)

        except Exception as e:
            raise RuntimeError(f"Failed to optimize LinkedIn message: {e}")
        
    def generate_follow_up_email_sections(self):
        """
        Generates a concise and professional follow-up email in JSON format using Anthropic API.

        Parameters:
        - ice_breaker (str): The initial engaging hook.
        - about_company (str): Information about the company.
        - call_to_action (str): The call to action prompting a response.
        - previous_email_subject (str): The subject line of the previous email.

        Returns:
        - dict: A dictionary containing the follow-up email components.
        """
        try:
            prompt = f"""
            Generate a concise and professional follow-up email sections using the given details.

            ### **Available Information:**
            - **Ice Breaker:** {self.b2b_sales_content.get('ice_breaker')}
            - **About Company:** {self.b2b_sales_content.get('client_value_proposition')}
            - **Call to Action:** {self.b2b_sales_content.get('call_to_action')}  
            - **Previous Email Subject:** {self.b2b_sales_content.get('subject')}  

            ### **Requirements:**
            1. Ensure the **tone is professional, friendly, and concise**, maintaining the context of a follow-up.  
            2. Provide a **reworded subject line** that aligns with the follow-up nature.  
            3. **Output Format:** A pure JSON string with the following keys:  
            - "ice_breaker_follow_up": Personalized follow-up opening line. 
                (Do not include greetings or recipient name)
            - "about_company_follow_up": A short, compelling summary of the about section of the company.
            - "call_to_action_follow_up": A follow-up request that is clear, inviting, and action-driven.  
            - "subject_follow_up": A refined, engaging follow-up subject line.  

            ### OUTPUT FORMAT
            The response **must** be in **pure JSON format** as the one given below with no additional text:
            {{
            "ice_breaker_follow_up": "",
            "about_company_follow_up": "",
            "call_to_action_follow_up": "",
            "subject_follow_up": ""
            }}

            The output should be pure JSON text without "json" before it.
            """

            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=3000,
                temperature=0.7,
                system="You are a professional email copywriter specializing in crafting concise and effective follow-up emails.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            content = response.content[0].text.strip()
            print(f"Follow-up content: {content}")
            return json.loads(content)

        except Exception as e:
            raise RuntimeError(f"Failed to generate follow-up email: {e}")
        
    def generate_follow_up_linkedin_message_sections(self):
        """
        Generates a concise and professional follow-up LinkedIn message in JSON format using Anthropic.

        Parameters:
        - ice_breaker (str): The initial engaging hook.
        - about_company (str): Information about the company.
        - call_to_action (str): The call to action prompting a response.
        - previous_email_subject (str): The subject line of the previous email.

        Returns:
        - dict: A dictionary containing the follow-up LinkedIn message components.
        """
        try:
            prompt = f"""
            Generate a concise and professional follow-up LinkedIn message sections using the given details.

            ### **Available Information:**
            - **Ice Breaker:** {self.b2b_sales_content.get('ice_breaker')}
            - **About Company:** {self.b2b_sales_content.get('client_value_proposition')}
            - **Call to Action:** {self.b2b_sales_content.get('call_to_action')}  
            - **Previous Email Subject:** {self.b2b_sales_content.get('subject')}  

            ### **Requirements:**
            1. **Rephrase** the about company section to be used for a suitable follow-up message for LinkedIn.  
            2. Ensure the **tone is professional, friendly, and concise**, maintaining the context of a follow-up.  
            3. Provide a **reworded subject line** that aligns with the follow-up nature.  
            4. **Output Format:** A pure JSON string with the following keys:  
            - "ice_breaker_linkedin_follow_up": Personalized follow-up opening line. 
            - "about_company_linkedin_follow_up": A short, compelling summary of the provided about section.
            - "call_to_action_linkedin_follow_up": A follow-up request that is clear, inviting, and action-driven.  
            - "subject_linkedin_follow_up": A refined, engaging follow-up subject line.  

            ### OUTPUT FORMAT
            The response **must** be in **pure JSON format** as the one given below with no additional text:
            {{
            "ice_breaker_linkedin_follow_up": "",
            "about_company_linkedin_follow_up": "",
            "call_to_action_linkedin_follow_up": "",
            "subject_linkedin_follow_up": ""
            }}

            The output should be pure JSON text without "json" before it.
            """

            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=3000,
                temperature=0.7,
                system="You are a professional LinkedIn message copywriter specializing in crafting concise and effective follow-up messages.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            content = response.content[0].text.strip()
            print(f"Follow-up LinkedIn content: {content}")
            return json.loads(content)

        except Exception as e:
            raise RuntimeError(f"Error occurred while generating follow-up LinkedIn message: {e}")

    def generate_linkedin_connection_message_sections(self):
        """
        Generates a concise and professional LinkedIn connection request message in JSON format using Anthropic.

        Parameters:
        - ice_breaker (str): Personalized opening line without greeting or recipient name.
        - about_company (str): Info about the company to be rephrased into one compelling sentence.
        - call_to_action (str): Action-oriented request.
        - previous_email_subject (str): Prior subject line to help shape the new subject.

        Returns:
        - dict: A dictionary with connection message components in JSON format.
        """
        try:
            prompt = f"""
            Generate a concise and professional LinkedIn connection request message sections using the given details.

            ### **Available Information:**
            - **Ice Breaker:** {self.b2b_sales_content.get('ice_breaker')}
            - **About Company:** {self.b2b_sales_content.get('client_value_proposition')}
            - **Call to Action:** {self.b2b_sales_content.get('call_to_action')}  
            - **Previous Email Subject:** {self.b2b_sales_content.get('subject')}  

            ### **Requirements:**
            1. Rephrase the about section into a single brief and compelling sentence for LinkedIn connection request.
            2. Ensure the tone is professional, friendly, and concise.
            3. Provide a reworded subject line that aligns with a LinkedIn connection request.

            ### OUTPUT FORMAT
            The response must be in pure JSON format as shown below with no additional text:
            {{
            "ice_breaker_connection_message": "",
            "about_company_connection_message": "",
            "call_to_action_connection_message": "",
            "subject_connection_message": ""
            }}
            """

            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=3000,
                temperature=0.7,
                system="You are a professional LinkedIn message copywriter.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            content = response.content[0].text.strip()
            return json.loads(content)

        except Exception as e:
            print(f"Error generating connection message content: {e}")
            raise RuntimeError("Error occurred while generating LinkedIn connection message sections")

    def generate_linkedin_connection_message(self):
        """
        Generates a concise LinkedIn connection request message from the provided email content using Anthropic.

        Parameters:
        - email_content (str): The content of the email to base the LinkedIn message on.

        Returns:
        - str: A LinkedIn connection message not exceeding 220 characters.
        """

        prompt = f"""
        Task:
        Generate a concise LinkedIn connection request message based on the content from the provided LinkedIn connection message content.

        Source:
        - LinkedIn connection message content: {self.linkedin_connection_message_content}, recipient name: {self.lead_info.get('recipient_first_name')}

        Objective:
        - Create a short, professional, and persuasive LinkedIn connection message that fits within LinkedIn’s 120-character limit.

        Requirements:
        - Strictly maximum 120 characters
        - Start with a greeting
        - Keep it brief, clear, and value-driven
        - Add a light, personable icebreaker
        - Use only the provided content
        - No signature or closing

        Output:
        - Only return the final LinkedIn message in plain text. Do not exceed 200 characters.
        """

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=3000,
                temperature=0.7,
                system="You are a professional copywriter specializing in LinkedIn outreach.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            message = response.content[0].text.strip()
            print(f"connection message generated: {message}")
            if len(message) > 300:
                raise ValueError("Generated message exceeds 300 characters.")
            return message

        except Exception as e:
            print(f"Error: {e}")
            raise RuntimeError("Error occurred while generating LinkedIn connection message")

generator_guideline = GuidelineGenerate()