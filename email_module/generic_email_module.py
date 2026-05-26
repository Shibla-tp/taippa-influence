import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Gmail Credentials
EMAIL_ADDRESS = 'shibla@taippa.com'
EMAIL_PASSWORD = 'rkecttakcyajughv'

def send_html_email(to_email, subject, html_content, cc_emails=None):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    if cc_emails:
        msg['Cc'] = ', '.join(cc_emails)

    # Attach HTML content
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)

    # Combine recipients
    recipients = [to_email] + (cc_emails if cc_emails else [])

    # Send the email via Gmail's SMTP server
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_ADDRESS, recipients, msg.as_string())
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
