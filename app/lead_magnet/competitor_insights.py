import os
import requests

# from error_logger import execute_error_block

def get_competitors_list(industry,country):

    # API endpoint and key
    url = "https://api.perplexity.ai/chat/completions"
    api_key = os.getenv("PERPLEXITY_API_KEY")  # Retrieve the API key from an environment variable

    if not api_key:
        return "Error: API key not found in environment variable PERPLEXITY_API_KEY"

    # Prompt for the Perplexity API
    prompt = f"""
    Find the top 5 competitors for the {industry} industry in {country} using credible sources specific to the country. Ensure the metrics provided are accurate and reasonable for the industry.

    Do not bold the headings, and ensure everything is presented as plain text.

    Provide the data in this exact concise format:
    1. Competitor Name 1: Short description. 
    2. Competitor Name 2: Short description.
    3. Competitor Name 3: Short description. 
    4. Competitor Name 4: Short description. 
    5. Competitor Name 5: Short description.

    - If specific data for the {industry} industry is unavailable, use data from a closely related industry.
    - Do not include sources, references, or explanations.
    - Avoid vague terms like 'not specified.' Provide reasonable and accurate estimates based on the industry.

    Output should be strictly text.
    """

    # Payload for the API request
    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {"role": "system", "content": "Be concise and only output the requested metrics. Do not include sources."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300,
        "temperature": 0.2,
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

    try:
        # Send the request
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()

        # Extract and format the content
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
        else:
            return "No content generated."
    except requests.exceptions.RequestException as e:
        return f"API request failed: {e}"

# Example usage
if __name__ == "__main__":
    industry = "information technology & services"  # Replace with the desired industry
    country= "Dubai, United Arab Emirates"
    competitors_list = get_competitors_list(industry,country)
    print(competitors_list)