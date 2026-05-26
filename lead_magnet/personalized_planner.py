
# from error_logger import execute_error_block

import os
import requests
from lead_magnet.client_info_parser import collect_information
# from lead_magnet.client_info_parser import collect_information

import os
import requests

def generate_personalized_planner(details):
    """
    Generates a 15-day planner to enhance productivity and sales for an organization using OpenAI's GPT-4 model.
    
    Args:
        details (dict): Organization details including name, industry, employee count, technologies, description, state, and country.
    
    Returns:
        str: The generated 15-day planner in JSON format or an error message.
    """

    # Retrieve API key securely
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Error: API key not found. Please set OPENAI_API_KEY as an environment variable."

    # Organization details with fallbacks
    organization_name = details.get('organization_name', 'the organization')
    organization_industry = details.get('organization_industry', 'the industry')
    organization_employee_count = details.get('organization_employee_count', 'N/A')
    organization_technologies = details.get('organization_technologies', 'various technologies')
    organization_description = details.get('organization_description', 'a growing company')
    organization_state = details.get('organization_state', 'N/A')
    organization_country = details.get('organization_country', 'N/A')

    # Optimized Prompt
    prompt = f"""
    Objective:
    Generate a **15-day structured planner** to enhance sales and growth for {organization_name}.

    **Organization Profile:**
    - **Name:** {organization_name}
    - **Industry:** {organization_industry}
    - **Employees:** {organization_employee_count}
    - **Technologies Used:** {organization_technologies}
    - **Description:** {organization_description}
    - **Location:** {organization_state}, {organization_country}

    **Planner Requirements:**
    - **Each day's plan must have a title and actionable steps.**
    - **Ensure strategies are aligned with {organization_industry} and company size.**
    - **Provide specific, measurable tasks to improve sales and business growth.**
    - **Avoid generic suggestions; customize recommendations based on the given details.**
    - **The output should be structured in valid JSON format** with **no additional text**.

    **Example JSON Structure:**
    {{
        "Day 1: [Title]": {{
            "Action items": [
                "[Specific Action 1]",
                "[Specific Action 2]",
                "[Specific Action 3]"
            ]
        }},
        "Day 2: [Title]": {{
            "Action items": [
                "[Specific Action 1]",
                "[Specific Action 2]",
                "[Specific Action 3]"
            ]
        }},
        ...
        "Day 15: [Title]": {{
            "Action items": [
                "[Specific Action 1]",
                "[Specific Action 2]",
                "[Specific Action 3]"
            ]
        }}
    }}
    """

    # API request payload
    payload = {
        "model": "gpt-4-turbo",  # Using GPT-4 Turbo for best performance
        "messages": [
            {"role": "system", "content": "You are an expert in sales and business strategy. Generate a structured 15-day planner strictly in JSON format."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4000,
        "temperature": 0.7,
        "top_p": 0.9,
    }

    # Headers with proper authorization format
    headers = {
        "Authorization": f"Bearer {api_key}",  # Ensure API key is correctly formatted
        "Content-Type": "application/json"
    }

    # Send API request with proper error handling
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        
        # Handle Unauthorized Error
        if response.status_code == 401:
            return "Error: Unauthorized. Please check your API key and ensure it is correct."

        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()

        # Parse response
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
        return "No content generated."
    
    except requests.exceptions.RequestException as e:
        return f"API request failed: {e}"


def generate_personalized_planner_v1(details):
    """
    Generates a 15-day planner to enhance productivity and sales for an organization using the Perplexity API.
    
    Args:
        industry (str): The organization's industry.
        employee_count (int): Number of employees in the organization.
        technologies (str): Technologies used by the organization.
        description (str): A brief description of the organization.
        country (str): The country where the organization operates.
    
    Returns:
        str: The generated 15-day planner or an error message.
    """

    organization_name = details.get('organization_name')
    organization_industry = details.get('organization_industry')
    organization_employee_count = details.get('organization_employee_count')
    organization_technologies = details.get('organization_technologies')
    organization_description = details.get('organization_description')
    organization_state = details.get('organization_state')
    organization_country = details.get('organization_country')

    # API endpoint and key
    url = "https://api.perplexity.ai/chat/completions"
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return "Error: API key not found in environment variable PERPLEXITY_API_KEY"


    latest_prompt_v2 = f"""
    Objective: 
    Create a 15-day sales improvement planner for {organization_name}.

    Organization Profile:
    - Name: {organization_name}
    - Industry: {organization_industry}
    - Employees: {organization_employee_count}
    - Technologies: {organization_technologies}
    - Description: {organization_description}
    - Location: {organization_state}, {organization_country}

    Approach:

    Step 1: Analyze Current Situation
    - Understand the organization-specific details provided.
    - Evaluate organizational details.
    - Assess the context.
    - Determine factors affecting sales in the {organization_industry} industry in {organization_country}.

    Step 2: Reasoning Process
    For each consideration:
    - Identify sales strategy implications based on the details mentioned in Step 1.
    - Connect insights to actionable steps.

    Step 3: Detailed Reasoning
    - Explain the decision-making process based on the reasoning.
    - Justify recommendations.
    - Establish logical connections between insights and actions.

    Deliverable:
    Provide a detailed 15-day planner tailored to {organization_name}'s characteristics and needs:
    - The content should dynamically align with:
    - Industry: {organization_industry}.
    - Organization size: {organization_employee_count}.
    - Technologies used: {organization_technologies}.
    - Description: {organization_description}.
    - Include specific, achievable daily goals.
    - Incorporate measurable milestones.
    - The output should only include the 15-day planner, with no additional content.
    - Ensure the plan is specific to individual days.

    Example Format:

    Day 1: [Heading]
    - Action items

    Day 2: [Heading]
    - Action items

    ... Similarly for all days ...

    Day 15: [Heading]
    - Action items

    The output should be only purely JSON text without formatting and without writing json before the actual json code.
    Just follow the output JSON text structure for the format as per the example below, but the content should be entirely different and specific to each organization:
    Example JSON text structure (example for 3 days, but the output should be for 15 days with different content):
    
    "
    {{
        "Day 1: [Some Title 1]": {{
            "Action items": [
                "[Action item 1]",
                "[Action item 2]",
                "[Action item 3]"
            ]
        }},
        "Day 2: [Some Title 2]": {{
            "Action items": [
                "[Action item 1]",
                "[Action item 2]",
                "[Action item 3]"
            ]
        }},
        "Day 3: [Some Title 3]": {{
            "Action items": [
                "[Action item 1]",
                "[Action item 2]",
                "[Action item 3]"
            ]
        }}
    }}
    "
     
    """

    # API request payload
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "Be concise and only output the requested metrics. Do not include sources."},
            {"role": "user", "content": latest_prompt_v2}
        ],
        "max_tokens": 2000,
        "temperature": 0.6,
        "top_p": 0.9,
        "search_domain_filter": ["perplexity.ai"],
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": "year",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1
    }

    # Headers with API key
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Send API request
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()

        # Parse response
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
        return "No content generated."
    except requests.exceptions.RequestException as e:
        return f"API request failed: {e}"

# Example usage
if __name__ == "__main__":
    industry = "information technology & services"  # Replace with the desired industry
    employee_count="2"
    technologies="['AI', 'Gmail', 'Google Apps', 'Google Cloud Hosting', 'Mobile Friendly', 'Remote', 'Varnish', 'Wix']"
    description="""
    CGNet was established as a representative of German Telecommunication & Payment Systems suppliers in Febr. 2006. It serves the MENA area encompassing the Middle East, North Africa, India, Pakistan and Sri Lanka regions.

    Information is a business's most important asset. CGNet provides the tools that can help you capitalize on it. By bringing our systems, software, services, and solutions together, we can work with you to put a comprehensive infrastructure to work for your business.
    """
    country= "Dubai, United Arab Emirates"

    # details = collect_information("nadia@cgnet.ae")
    details = collect_information("sravan.workemail@gmail.com")
    # details = collect_information("timofey.borzov@vtbcapital.com")
    # timofey.borzov@vtbcapital.com

    content = generate_personalized_planner(details)
    print(content)