import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from error_logger import execute_error_block

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def send_email(receiver_email: str, subject: str, body: str) -> str:
    """
    Send an email without any attachment.

    Args:
        receiver_email (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body text.

    Returns:
        str: Success or failure message.
    """
    sender_email = os.getenv("SENDER_EMAIL", "sravan@taippa.com")
    smtp_password = os.getenv("SMTP_PASSWORD", "gbvl bsgn aocv hymz")
    
    try:
        # Prepare email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, smtp_password)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {receiver_email}")
        return f"Email successfully sent to {receiver_email}"
    
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email: {e}")
        return "Failed to send email. Please try again later."
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}")
        return "Failed to send email. Please try again later."

def login_email_sender(recipient_name,recipient_email,user_id,password):
    try:
        login_page = "https://taippa.com/login/"
        subject = "Your Campaign is Live – Access Your Account Now"
        body = f"""
Dear {recipient_name},

We are pleased to inform you that your lead generation campaign has been successfully set up. You can now access your dashboard and monitor lead insights in real time.

Your Login Credentials:
Username: {user_id}
Password: {password}
To access your account, please visit the following link:
🔗 Login Here: {login_page}

We appreciate your partnership with us and are excited to support your business growth. If you have any questions or need assistance, feel free to reach out.

Best regards,
Team Taippa

    """
        print(send_email(recipient_email, subject, body))
    
    except Exception as e:
        execute_error_block(f"Error occured while sending confirmation email: {e}")

if __name__ == "__main__":
    login_email_sender(recipient_name='Sravan',recipient_email='sravzone@gmail.com',user_id='sravz',password='israv')
    pass