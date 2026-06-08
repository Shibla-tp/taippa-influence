import os
import smtplib
import requests
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pyairtable import Api
from typing import Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AirtableEmailSender:
    def __init__(self):
        # Load environment variables
        self.airtable_api_key = os.getenv("AIRTABLE_API_KEY")
        self.airtable_base_id = os.getenv("AIRTABLE_BASE_ID")
        self.airtable_table_name = "lead_magnet_details_copy"

        # Email configuration
        self.sender_email = os.getenv("SENDER_EMAIL", "mohammed@taippa.com")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "ujda qovk dhzh qxua")

        # Validate required environment variables
        self._validate_env_vars()
        # Initialize Airtable API
        self.api = Api(self.airtable_api_key)
        self.table = self.api.table(self.airtable_base_id, self.airtable_table_name)

        # Verify Airtable connection and table existence
        self._verify_airtable_connection()

    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        required_vars = {
            "AIRTABLE_API_KEY": self.airtable_api_key,
            "AIRTABLE_BASE_ID": self.airtable_base_id,
            "SENDER_EMAIL": self.sender_email,
            "SMTP_PASSWORD": self.smtp_password
        }

        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

    def _verify_airtable_connection(self) -> None:
        """Verify Airtable connection and table existence."""
        try:
            # Try to get first record to verify connection and table existence
            records = self.table.all(max_records=1)
            logger.info(f"Successfully connected to Airtable table: {self.airtable_table_name}")
            logger.info(f"Base ID: {self.airtable_base_id}")

            if records:
                logger.info(f"Successfully found records in table")
                # Log record ID of first record to help with debugging
                logger.info(f"First record ID: {records[0]['id']}")
            else:
                logger.warning(f"Table exists but contains no records")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Table '{self.airtable_table_name}' not found in base '{self.airtable_base_id}'")
                logger.error("Please verify your base ID and table name")
            elif e.response.status_code == 403:
                logger.error("Authentication failed. Please verify your Airtable API key")
            else:
                logger.error(f"HTTP Error accessing Airtable: {e.response.status_code} - {e.response.text}")
            return "Oops! It seems our server is a bit busy right now. Please try again shortly."
            # raise

    def fetch_pdf_from_airtable(self, id_value: str) -> str:
        """
        Fetch PDF URL from Airtable record by matching the 'id' field.

        Args:
            id_value: The value to match in the 'id' field

        Returns:
            str: URL of the PDF file

        Raises:
            ValueError: If no PDF is found in the record
            requests.exceptions.HTTPError: If there's an error accessing Airtable
        """
        try:
            logger.info(f"Searching for record with id: {id_value}")

            # Search for records where id matches
            formula = f"{{id}} = '{id_value}'"
            records = self.table.all(formula=formula)

            if not records:
                raise ValueError(f"No record found with id: {id_value}")

            if len(records) > 1:
                logger.warning(f"Found multiple records ({len(records)}) with id: {id_value}")

            record = records[0]
            logger.info(f"Record found. Available fields: {list(record['fields'].keys())}")

            attachments = record['fields'].get('lead_magnet_pdf', [])
            logger.info(f"Found {len(attachments)} attachments in lead_magnet_pdf field")

            if not attachments:
                raise ValueError(f"No PDF found in record with id: {id_value}")

            url = attachments[0]['url']
            logger.info(f"Successfully retrieved PDF URL: {url[:50]}...")
            return url

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error accessing Airtable: {e.response.status_code} - {e.response.text}")
            return "Oops! It seems our server is a bit busy right now. Please try again shortly."
            raise
        except KeyError as e:
            logger.error(f"Missing field in Airtable record: {e}")
            logger.error("Please verify that 'lead_magnet_pdf' field exists and contains attachments")
            raise
            return "Oops! It seems our server is a bit busy right now. Please try again shortly."
    def download_pdf(self, pdf_url: str, save_path: Path) -> None:
        """
        Download PDF file from URL.

        Args:
            pdf_url: URL of the PDF file
            save_path: Path where the PDF should be saved
        """
        try:
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()

            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(response.content)

            logger.info(f"PDF downloaded successfully to {save_path}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading PDF: {e}")
            return "Oops! It seems our server is a bit busy right now. Please try again shortly."
            raise

    def send_email(self, receiver_email: str, subject: str, body: str,
                   pdf_path: Path, cleanup: bool = True) -> None:
        """
        Send email with PDF attachment.

        Args:
            receiver_email: Recipient's email address
            subject: Email subject
            body: Email body text
            pdf_path: Path to the PDF file to attach
            cleanup: Whether to delete the PDF file after sending
        """


        print(f"pdf_path : {pdf_path}")

        if not pdf_path.exists():
            # return "Oops! Seems like our server is little busy"
            print(f"PDF file not found at {pdf_path}")
            return "Oops! It seems our server is a bit busy right now. Please try again shortly."
            # raise FileNotFoundError(f"PDF file not found at {pdf_path}")

        try:
            # Prepare email
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = receiver_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Attach PDF
            with pdf_path.open('rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={pdf_path.name}"
                )
                msg.attach(part)

            # Send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.sender_email, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {receiver_email}")

            # # Cleanup
            # if cleanup:
            #     pdf_path.unlink()
            #     logger.info(f"Temporary PDF file removed: {pdf_path}")

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            return "Invalid Email ID"
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return "Invalid Email ID"
            raise

def main(recipient_email_id,user_details,final_pdf):
    try:
        sender = AirtableEmailSender()

        # Configuration
        id_to_search = "66a0bdc2aa61c20001776e82"  # The ID value to search for
        receiver_email = recipient_email_id
        print(receiver_email)
        company_name = user_details.get('organization_name','your company')
        name = user_details.get('name','Sir')
        title = user_details.get('title','professional')
        subject = f"15-day Sales Booster for {company_name}"

        body = f"""
        Dear {name},


        I hope you're doing well.

        We have something exciting for you – The "15-day Sales Booster Plan for {company_name}".

        If you have any questions or need further assistance, don’t hesitate to reach out.


        Best regards,

        Team Taippa

        +971-293284822

        """

        # body = "Please find attached the PDF you requested."

        # pdf_path = Path("pdf/lead_magnet_personalized.pdf")
        pdf_path = Path(final_pdf)
        # Process
        # pdf_url = sender.fetch_pdf_from_airtable(id_to_search)
        # sender.download_pdf(pdf_url, pdf_path)
        # pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),"pdf/lead_magnet_personalized.pdf")
        # pdf_path = Path(pdf_path)
        sender.send_email(receiver_email, subject, body, pdf_path)
        logger.info("Process completed successfully")
        return f"Email successfully sent to {recipient_email_id}"

    except Exception as e:
        logger.error(f"Process failed: {e}")
        return "Invalid Email ID"

def send_lead_magnet_email(recipient_email_id,user_details,final_pdf):
    return main(recipient_email_id,user_details,final_pdf)

if __name__ == "__main__":
    pass
    # send_lead_magnet_email()