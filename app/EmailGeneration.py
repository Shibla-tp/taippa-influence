"""
Email Generation System - Complete Implementation
Matches all Make.com scenario functionality including multiple table management,
robust error handling, and complete workflow alignment.
"""

import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from time import sleep
import openai
import colorama
from colorama import Fore, Style
import requests
import json
from typing import Dict

# Initialize colorama
colorama.init()

class DebugLogger:
    def __init__(self, name: str):
        self.name = name

    def info(self, message: str):
        print(f"{Fore.GREEN}[INFO] {self.name}: {message}{Style.RESET_ALL}")

    def debug(self, message: str):
        print(f"{Fore.BLUE}[DEBUG] {self.name}: {message}{Style.RESET_ALL}")

    def error(self, message: str):
        print(f"{Fore.RED}[ERROR] {self.name}: {message}{Style.RESET_ALL}")

    def success(self, message: str):
        print(f"{Fore.GREEN}[SUCCESS] {self.name}: {message}{Style.RESET_ALL}")

    def warning(self, message: str):
        print(f"{Fore.YELLOW}[WARNING] {self.name}: {message}{Style.RESET_ALL}")

    def step(self, message: str):
        print(f"{Fore.CYAN}[STEP] {self.name}: {message}{Style.RESET_ALL}")


@dataclass
class LeadData:
    # Required field with a default value to prevent initialization errors
    unique_id: str
    recipient_first_name: str = ''
    recipient_last_name: str = ''
    recipient_role: str = ''
    recipient_company: str = ''
    recipient_email: str = ''

    # Optional fields
    recipient_bio: Optional[str] = None
    employment_summary: Optional[str] = None
    associated_client_id: Optional[str] = None
    outreach_table: Optional[str] = None
    sender_name: Optional[str] = None
    sender_title: Optional[str] = None
    sender_company: Optional[str] = None
    sender_email: Optional[str] = None
    sender_company_website: Optional[str] = None
    key_benefits: Optional[str] = None
    unique_features: Optional[str] = None
    impact_metrics: Optional[str] = None
    cta_options: Optional[str] = None
    color_scheme: Optional[str] = None
    font_style: Optional[str] = None

def process_single_lead(self, lead_record: Dict):
    """Process a single lead and update its processed status"""
    try:
        # Extract lead data with validation
        fields = lead_record.get('fields', {})

        # Check for required fields before processing
        required_fields = ['recipient_first_name', 'recipient_last_name', 'recipient_role',
                           'recipient_company', 'recipient_email']

        missing_fields = [field for field in required_fields
                          if not fields.get(field)]

        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            self.logger.error(error_msg)

            # Update record to mark as processed with error
            error_fields = {
                'processed': 'true',
                'processed_date': datetime.now(timezone.utc).isoformat(),
                'instantly_status': 'Error',
                'error_message': error_msg
            }

            self.retry_handler.retry_operation(
                self.airtable.update_record,
                'outreach_berkleys',
                lead_record['id'],
                error_fields
            )
            return

        # Create LeadData object with validated fields
        lead = LeadData(
            unique_id=lead_record['id'],
            recipient_first_name=fields.get('recipient_first_name', ''),
            recipient_last_name=fields.get('recipient_last_name', ''),
            recipient_role=fields.get('recipient_role', ''),
            recipient_company=fields.get('recipient_company', ''),
            recipient_email=fields.get('recipient_email', ''),
            recipient_bio=fields.get('recipient_bio'),
            employment_summary=fields.get('employment_summary'),
            associated_client_id=fields.get('associated_client_id'),
            outreach_table=fields.get('outreach_table'),
            sender_name=fields.get('sender_name'),
            sender_title=fields.get('sender_title'),
            sender_company=fields.get('sender_company'),
            sender_email=fields.get('sender_email'),
            sender_company_website=fields.get('sender_company_website'),
            key_benefits=fields.get('key_benefits'),
            unique_features=fields.get('unique_features'),
            impact_metrics=fields.get('impact_metrics'),
            cta_options=fields.get('cta_options'),
            color_scheme=fields.get('color_scheme'),
            font_style=fields.get('font_style')
        )

        # Rest of your processing code...

    except Exception as e:
        self.logger.error(f"Error processing lead: {str(e)}")
        # Update record with error status
        error_fields = {
            'processed': 'true',
            'processed_date': datetime.now(timezone.utc).isoformat(),
            'instantly_status': 'Error',
            'error_message': str(e)
        }
        try:
            self.retry_handler.retry_operation(
                self.airtable.update_record,
                'outreach_berkleys',
                lead_record['id'],
                error_fields
            )
        except Exception as update_error:
            self.logger.error(f"Failed to update error status: {str(update_error)}")

class RetryHandler:
    """Handles retrying operations with exponential backoff"""

    def __init__(self, max_retries: int = 3, base_delay: int = 15):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.logger = DebugLogger("RetryHandler")

    def retry_operation(self, operation_func, *args, **kwargs):
        """Retries an operation with exponential backoff"""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return operation_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.max_retries - 1:
                    raise e

                delay = self.base_delay * (2 ** attempt)
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay} seconds...")
                sleep(delay)

        if last_exception:
            raise last_exception

class AirtableManager:
    def __init__(self, api_key: str, base_id: str):
        self.logger = DebugLogger("Airtable")
        self.api_key = api_key
        self.base_id = base_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.logger.success("Initialized AirtableManager")

    def get_new_leads(self, table_name: str, filter_formula: str = None) -> List[Dict]:
        """Gets new leads from the specified table with optional filter"""
        self.logger.step("Fetching new leads")
        url = f"https://api.airtable.com/v0/{self.base_id}/{table_name}"

        params = {
            'maxRecords': 15,  # Matching Make.com scenario limit
            'sort[0][field]': 'created_date',
            'sort[0][direction]': 'desc'
        }

        # Add filter if provided
        if filter_formula:
            params['filterByFormula'] = filter_formula

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            records = response.json().get('records', [])
            self.logger.success(f"Found {len(records)} new leads")
            return records
        except Exception as e:
            self.logger.error(f"Error getting leads: {e}")
            return []

    def get_client_details(self, client_id: str) -> Optional[Dict]:
        """Gets client details from the client_info table"""
        self.logger.step(f"Getting client details for {client_id}")
        url = f"https://api.airtable.com/v0/{self.base_id}/client_info"

        params = {
            'filterByFormula': f"{{client_id}} = '{client_id}'",
            'maxRecords': 1
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            records = response.json().get('records', [])
            if records:
                self.logger.success("Found client details")
                return records[0]
            self.logger.warning("No client details found")
            return None
        except Exception as e:
            self.logger.error(f"Error getting client details: {e}")
            return None

    def update_record(self, table_name: str, record_id: str, fields: Dict) -> bool:
        """Updates an existing record"""
        self.logger.step(f"Updating record {record_id}")
        url = f"https://api.airtable.com/v0/{self.base_id}/{table_name}/{record_id}"

        # Clean and validate fields
        cleaned_fields = {}
        for key, value in fields.items():
            # Convert empty strings to None
            if value == "":
                cleaned_fields[key] = None
            # Ensure strings don't exceed Airtable's limit (100,000 characters)
            elif isinstance(value, str) and len(value) > 100000:
                cleaned_fields[key] = value[:100000]
            else:
                cleaned_fields[key] = value

        try:
            payload = {'fields': cleaned_fields}
            self.logger.debug(f"Update payload: {json.dumps(payload, indent=2)}")

            response = requests.patch(url, headers=self.headers, json=payload)

            if response.status_code == 422:
                error_detail = response.json()
                self.logger.error(f"Airtable validation error: {error_detail}")
                return False

            response.raise_for_status()
            self.logger.success(f"Updated record {record_id}")
            return True
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error updating record: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.debug(f"Error response: {e.response.text}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error updating record: {str(e)}")
            return False
    def create_record(self, table_name: str, fields: Dict) -> Optional[str]:
        """Creates a new record in specified table"""
        self.logger.step(f"Creating record in {table_name}")
        url = f"https://api.airtable.com/v0/{self.base_id}/{table_name}"

        try:
            payload = {
                'records': [{
                    'fields': fields
                }]
            }
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            record_id = response.json()['records'][0]['id']
            self.logger.success(f"Created record {record_id}")
            return record_id
        except Exception as e:
            self.logger.error(f"Error creating record: {e}")
            return None
        
class PerplexityEnricher:
    def __init__(self, api_key: str):
        self.logger = DebugLogger("Perplexity")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.logger.success("Initialized PerplexityEnricher")

    def enrich_lead(self, lead: LeadData) -> str:
        """Enriches lead data with additional research"""
        self.logger.step(f"Enriching lead data for {lead.recipient_first_name}")
        url = "https://api.perplexity.ai/chat/completions"

        prompt = f"""
        Information about lead:
        Role: {lead.recipient_role}
        Name: {lead.recipient_first_name} {lead.recipient_last_name}
        Bio: {lead.recipient_bio}
        Company: {lead.recipient_company}
        Employment: {lead.employment_summary}

        Search about this person and their company on the internet and social media pages.
        Find information that can be used as an ice breaker for cold email outreach.
        Focus on recent achievements, company news, or professional interests.
        """

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json={
                    "model": "llama-3.1-sonar-huge-128k-online",
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            self.logger.error(f"Error enriching lead: {e}")
            return ""


class EmailGenerator:
    def __init__(self, api_key: str):
        self.logger = DebugLogger("EmailGen")
        self.api_key = api_key
        openai.api_key = api_key
        self.logger.success("Initialized EmailGenerator")

    def generate_content(self, lead: LeadData, client_data: Dict, enriched_data: str) -> Dict[str, str]:
        """Generates email content using the template"""
        self.logger.step(f"Generating email for {lead.recipient_first_name}")

        try:
            prompt = f"""Generate a cold outreach email.

Return ONLY a JSON object with this exact structure:
{{
    "Subject": "The email subject line",
    "Email_Body": "The main email body",
    "Follow_up": "The follow-up email content"
}}

Recipient Information:
- Name: {lead.recipient_first_name} {lead.recipient_last_name}
- Role: {lead.recipient_role}
- Company: {lead.recipient_company}
- Bio: {lead.recipient_bio}

Client Information:
- Benefits: {client_data.get('solution_benefits', '')}
- Features: {client_data.get('unique_features', '')}
- Domain: {client_data.get('domain', '')}
- Business Type: {client_data.get('business_type', '')}

Additional Context:
{enriched_data}

The email should:
1. Start with a personalized ice breaker
2. Show clear relevance to the recipient
3. Address specific pain points
4. Use industry-specific language
5. Have a clear call to action
6. Include proper signature with all sender details

Sign off with:
{lead.sender_name}
{lead.sender_title}
{lead.sender_company}
{lead.sender_company_website}"""

            # Make the API call with explicit formatting
            # response = openai.ChatCompletion.create(
            #     model="gpt-4",
            #     messages=[{
            #         "role": "system",
            #         "content": "You are a professional email writer. Always return responses in valid JSON format."
            #     }, {
            #         "role": "user",
            #         "content": prompt
            #     }],
            #     temperature=0.7,
            #     max_tokens=2000
            # )

            # content = response.choices[0].message.content.strip()
            
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{
                    "role": "system",
                    "content": "You are a professional email writer. Always return responses in valid JSON format."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.7,
                max_tokens=2000
            )
            # print(response.choices[0].message.content)
            content = response.choices[0].message.content

            try:
                email_content = json.loads(content)
                self.logger.success("Generated email content")
                return email_content
            except json.JSONDecodeError as je:
                self.logger.error(f"JSON parsing error: {je}")
                self.logger.debug(f"Raw content that failed to parse: {content}")
                return {
                    "Subject": "Error Generating Email",
                    "Email_Body": "Error generating email content",
                    "Follow_up": "Error generating follow-up content"
                }

        except Exception as e:
            self.logger.error(f"Error generating email: {str(e)}")
            return {
                "Subject": "Error Generating Email",
                "Email_Body": "Error generating email content",
                "Follow_up": "Error generating follow-up content"
            }


class InstantlyManager:
    def __init__(self, api_key: str):
        self.logger = DebugLogger("Instantly")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.instantly.ai/api/v2"
        self.logger.success("Initialized InstantlyManager")

    def add_to_campaign(self, campaign_id: str, lead: 'LeadData', email_content: Dict[str, str]) -> bool:
        """Adds a lead to an email campaign"""
        url = f"{self.base_url}/leads"

        # Prepare payload exactly as per working example
        payload = {
            "campaign": campaign_id,
            "email": lead.recipient_email,
            "personalization": f"Hi {{first_name}}, I noticed your work at {{company_name}}",
            "website": lead.sender_company_website or "",
            "last_name": lead.recipient_last_name,
            "first_name": lead.recipient_first_name,
            "company_name": lead.recipient_company,
            "payload": {
                "firstName": lead.recipient_first_name,
                "lastName": lead.recipient_last_name,
                "companyName": lead.recipient_company,
                "website": lead.sender_company_website or "",
                "personalization": f"Hi {{first_name}}, I noticed your work at {{company_name}}",
                "email": lead.recipient_email,
                "campaign": campaign_id,
                "Subject": email_content.get('Subject', ''),
                "EmailBody": email_content.get('Email_Body', ''),
                "FollowUp": email_content.get('Follow_up', '')
            },
            "skip_if_in_workspace": True,
            "skip_if_in_campaign": True,
            "verify_leads_on_import": True
        }

        try:
            self.logger.debug(f"Sending payload to {url}: {json.dumps(payload, indent=2)}")

            response = requests.post(url, headers=self.headers, json=payload)

            self.logger.debug(f"Response status code: {response.status_code}")
            self.logger.debug(f"Response text: {response.text}")

            if response.status_code == 200:
                response_data = response.json()
                self.logger.success("Successfully added lead to campaign")
                return True
            else:
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('message', 'Unknown error')
                        self.logger.error(f"API Error: {error_msg}")
                    except ValueError:
                        self.logger.error(f"Error response: {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"Error adding lead to campaign: {str(e)}")
            return False
class LeadProcessor:
    def __init__(self, api_keys: Dict[str, str]):
        self.logger = DebugLogger("LeadProcessor")

        # Extract required API keys
        airtable_key = api_keys.get('airtable_api_key')
        perplexity_key = api_keys.get('perplexity_api_key')
        openai_key = api_keys.get('openai_api_key')
        instantly_key = api_keys.get('instantly_api_key')
        base_id = api_keys.get('airtable_base_id')

        if not all([airtable_key, perplexity_key, openai_key, instantly_key, base_id]):
            raise ValueError("Missing required API keys")

        # Initialize components
        self.logger.step("Initializing components...")
        self.retry_handler = RetryHandler()
        self.airtable = AirtableManager(airtable_key, base_id)
        self.perplexity = PerplexityEnricher(perplexity_key)
        self.email_gen = EmailGenerator(openai_key)
        self.instantly = InstantlyManager(instantly_key)
        self.logger.success("All components initialized")

    def get_unprocessed_leads(self) -> List[Dict]:
        """Gets leads that haven't been processed yet"""
        self.logger.step("Fetching unprocessed leads")
        try:
            # Get new leads with retry, adding filter for unprocessed leads
            leads = self.retry_handler.retry_operation(
                self.airtable.get_new_leads,
                'outreach_berkleys',
                filter_formula="{processed} = ''"  # Filter for empty processed column
            )
            self.logger.success(f"Found {len(leads)} unprocessed leads")
            return leads
        except Exception as e:
            self.logger.error(f"Error getting unprocessed leads: {str(e)}")
            return []

    def process_single_lead(self, lead_record: Dict):
        """Process a single lead and update its processed status"""
        try:
            # Extract lead data with validation
            fields = lead_record.get('fields', {})

            # Check for required fields before processing
            required_fields = ['recipient_first_name', 'recipient_last_name', 'recipient_role',
                               'recipient_company', 'recipient_email']

            missing_fields = [field for field in required_fields
                              if not fields.get(field)]

            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                self.logger.error(error_msg)

                # Update record to mark as processed with error
                error_fields = {
                    'processed': 'true',
                    'processed_date': datetime.now(timezone.utc).isoformat(),
                    'instantly_status': 'Error',
                    'error_message': error_msg
                }

                self.retry_handler.retry_operation(
                    self.airtable.update_record,
                    'outreach_berkleys',
                    lead_record['id'],
                    error_fields
                )
                return

            # Create LeadData object with validated fields
            lead = LeadData(
                unique_id=lead_record['id'],
                recipient_first_name=fields.get('recipient_first_name', ''),
                recipient_last_name=fields.get('recipient_last_name', ''),
                recipient_role=fields.get('recipient_role', ''),
                recipient_company=fields.get('recipient_company', ''),
                recipient_email=fields.get('recipient_email', ''),
                recipient_bio=fields.get('recipient_bio'),
                employment_summary=fields.get('employment_summary'),
                associated_client_id=fields.get('associated_client_id'),
                outreach_table=fields.get('outreach_table'),
                sender_name=fields.get('sender_name'),
                sender_title=fields.get('sender_title'),
                sender_company=fields.get('sender_company'),
                sender_email=fields.get('sender_email'),
                sender_company_website=fields.get('sender_company_website'),
                key_benefits=fields.get('key_benefits'),
                unique_features=fields.get('unique_features'),
                impact_metrics=fields.get('impact_metrics'),
                cta_options=fields.get('cta_options'),
                color_scheme=fields.get('color_scheme'),
                font_style=fields.get('font_style')
            )

            # Step 1: Get client data with retry
            client_data = self.retry_handler.retry_operation(
                self.airtable.get_client_details,
                lead.associated_client_id
            )

            if not client_data:
                error_msg = f"No client data found for {lead.associated_client_id}"
                self.logger.warning(error_msg)
                self.update_lead_with_error(lead_record['id'], error_msg)
                return

            # Step 2: Enrich lead data with retry
            enriched_data = self.retry_handler.retry_operation(
                self.perplexity.enrich_lead,
                lead
            )

            # Step 3: Generate email content with retry
            email_content = self.retry_handler.retry_operation(
                self.email_gen.generate_content,
                lead,
                client_data['fields'],
                enriched_data
            )

            if not email_content:
                error_msg = "Failed to generate email content"
                self.logger.error(error_msg)
                self.update_lead_with_error(lead_record['id'], error_msg)
                return

            # Step 4: Try to add to Instantly campaign
            campaign_success = self.retry_handler.retry_operation(
                self.instantly.add_to_campaign,
                "22795e87-2a6f-49be-b007-6f7f21840b05",
                lead,
                email_content
            )

            # Step 5: Update the record with results
            update_fields = {
                'subject': email_content.get('Subject', ''),
                'email': email_content.get('Email_Body', ''),  # Changed from email_body to email
                'follow_up': email_content.get('Follow_up', ''),
                'processed': 'true',
                'processed_date': datetime.now(timezone.utc).isoformat(),
                'instantly_status': 'Success' if campaign_success else 'Failed',
                'enriched_data': enriched_data
            }

            update_success = self.retry_handler.retry_operation(
                self.airtable.update_record,
                'outreach_berkleys',
                lead_record['id'],
                update_fields
            )

            if update_success:
                self.logger.success(f"Successfully processed lead {lead_record['id']}")
            else:
                self.logger.error(f"Failed to update lead record {lead_record['id']}")

        except Exception as e:
            self.logger.error(f"Error processing lead: {str(e)}")
            self.update_lead_with_error(lead_record['id'], str(e))

    def update_lead_with_error(self, record_id: str, error_message: str):
        """Helper method to update a lead record with error status"""
        error_fields = {
            'processed': 'true',
            'processed_date': datetime.now(timezone.utc).isoformat(),
            'instantly_status': 'Error',
            'error_message': error_message
        }
        try:
            self.retry_handler.retry_operation(
                self.airtable.update_record,
                'outreach_berkleys',
                record_id,
                error_fields
            )
        except Exception as update_error:
            self.logger.error(f"Failed to update error status: {str(update_error)}")

    def process_leads(self):
        """Process all unprocessed leads"""
        self.logger.step("Starting lead processing")

        try:
            # Get only unprocessed leads
            leads = self.get_unprocessed_leads()

            for lead in leads:
                try:
                    self.process_single_lead(lead)
                except Exception as e:
                    self.logger.error(f"Error processing lead {lead.get('id', 'unknown')}: {e}")
                    continue

            self.logger.success(f"Completed processing {len(leads)} leads")

        except Exception as e:
            self.logger.error(f"Fatal error in lead processing: {e}")
def main():
    logger = DebugLogger("Main")

    # Load configuration
    config = {
        'airtable_api_key': os.getenv('AIRTABLE_API_KEY'),
        'perplexity_api_key': os.getenv('PERPLEXITY_API_KEY'),
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'instantly_api_key': os.getenv('INSTANTLY_API_KEY'),
        'airtable_base_id': 'app5s8zl7DsUaDmtx'
    }

    # Validate configuration
    missing_keys = [k for k, v in config.items() if not v]
    if missing_keys:
        logger.error(f"Missing configuration keys: {', '.join(missing_keys)}")
        return

    try:
        processor = LeadProcessor(config)
        processor.process_leads()
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()