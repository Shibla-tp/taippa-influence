from flask import Flask
import csv
import requests
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

app = Flask(__name__)

# Airtable Configuration
AIRTABLE_API_KEY = 'patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3'
BASE_ID = 'app5s8zl7DsUaDmtx'
TABLE_NAME = 'leads_guideline'
CSV_FILE = 'leads_guideline.csv'

# Gmail Configuration
EMAIL_ADDRESS = 'shibla@taippa.com'
EMAIL_PASSWORD = 'rkecttakcyajughv'
TO_EMAIL = 'shiblashilu@gmail.com'
CC_EMAILS = ['shilusaifshilu@gmail.com', 'sravan@taippa.com']

def get_current_week_range():
    today = datetime.utcnow().date()
    weekday = today.weekday()  # Monday is 0, Sunday is 6
    # Saturday = 5 if we assume Sunday=6 (Python default)
    days_since_saturday = (today.weekday() + 2) % 7  # Saturday as start of week
    start = today - timedelta(days=days_since_saturday)
    end = start + timedelta(days=6)
    return start, end

def generate_csv_and_send_email():
    # Fetch data from Airtable
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}'
    headers = {'Authorization': f'Bearer {AIRTABLE_API_KEY}'}

    records = []
    offset = None
    while True:
        params = {'offset': offset} if offset else {}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return f"Failed to fetch Airtable data: {response.text}", 500
        data = response.json()
        records.extend(data['records'])
        offset = data.get('offset')
        if not offset:
            break

    if not records:
        return "No records found.", 404

    # Filter records for Saturday to Friday of the current week
    start_date, end_date = get_current_week_range()
    filtered_records = []
    for record in records:
        date_str = record['fields'].get('created_time')  # Replace 'Date' with your actual field name
        if date_str:
            try:
                record_date = datetime.strptime(date_str[:10], '%Y-%m-%d').date()
                if start_date <= record_date <= end_date:
                    filtered_records.append(record)
            except ValueError:
                continue  # skip if date format is invalid

    if not filtered_records:
        return "No records in this week's range.", 404

    # Write to CSV
    fieldnames = list(filtered_records[0]['fields'].keys())
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in filtered_records:
            writer.writerow(record['fields'])

    # Send Email
    msg = EmailMessage()
    msg['Subject'] = 'Leads Guideline CSV - Weekly Report'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg['Cc'] = ', '.join(CC_EMAILS)
    msg.set_content(f'Attached is the leads_guideline CSV file for {start_date} to {end_date}.')

    with open(CSV_FILE, 'rb') as f:
        msg.add_attachment(f.read(), maintype='text', subtype='csv', filename=f.name)

    recipients = [TO_EMAIL] + CC_EMAILS
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg, to_addrs=recipients)

    return f"CSV for {start_date} to {end_date} created and email sent successfully."
