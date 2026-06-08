from db.db_ops import db_manager 
import openai
from config import OPENAI_API_KEY
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def classify_email_message(reply_text):
    system_prompt = """You are an AI agent designed to analyze LinkedIn messages from leads and classify them as either "Positive" or "Negative".

Classification Criteria:

Positive:
- Agreement or enthusiasm
- Requests for more details or next steps
- Expressions of approval

Negative:
- Direct rejections or disagreements
- Requests to be removed from communication
- Neutral responses that do not show interest

Rules:
- If the message shows any level of interest, classify it as "Positive."
- If the message is neutral or negative in tone, classify it as "Negative."
- Do not classify ambiguous messages as "Positive" unless there is a clear intent to engage.

Output:
Return only one of the following labels:
1) Positive
2) Negative
"""

    user_prompt = f'This is the Email message text received from the lead: "{reply_text}"\n\nClassify this message based on the criteria.'

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()

def format_email_conversation(reply_text):
    system_prompt = (
        "You're going to be fed an email conversation.\n"
        "Your output should be the conversation formatted for human readability.\n"
        "Your output should be purely the conversation formatted and NOTHING ELSE."
    )

    user_prompt = f"Conversation:\n{reply_text}"

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()

def email_post_response_tracker():
    try:
        data = {
            "Campaign ID": "8f863581-3c23-4e7b-ba28-f078afaf4578",
            "Lead Email": "katie.hiatt@aspireiq.com",
            "Campaign Name": "GuidelineInfluencer", 
            "reply_text" : "Thanks for reaching out, but we are not interested at the moment."
            # "personalization": "Hi Taylor",
            # "FollowUpEmail" : "Hello Taylor",
            # "step": "2", 
        }
        sentiment = classify_email_message(data["reply_text"])
        print("Classification:", sentiment)
        formated_reply = format_email_conversation(data["reply_text"])
        # Step 1: Fetch client info using campaign ID
        cols_list = ['instantly_campaign_id']
        col_values = [data["Campaign ID"]]
        client_details = db_manager.get_records_with_filter("client_info", cols_list, col_values, limit=10)

        if not client_details:
            print("⚠️ No client found with the given campaign ID.")
            return

        print(f"🔢 Client Details: {client_details}")

        cleaned_table = client_details.get("cleaned_table")
        # outreach_table = client_details.get("outreach_table")
        if not cleaned_table:
            print("⚠️ 'cleaned_table' key not found in client details.")
            return

        print(f"✅ Cleaned Table: {cleaned_table}")
        # print(f"✅ Outreach Table: {outreach_table}")
        

        # Step 2: Fetch lead info using email
        lead_cols = ['email']
        lead_values = [data["Lead Email"]]
        lead_records = db_manager.get_records_with_filter(cleaned_table, lead_cols, lead_values, limit=10)
        print(f"Lead Records: {lead_records}")
        metrics_records = db_manager.get_records_with_filter(
            "metrics", ["campaign_id"], [data["Campaign ID"]], limit=10
        )
        if metrics_records:
            print(f"Metrics Record: {metrics_records}")
            metrics = metrics_records

            try:
                updated_count = int(metrics.get("replies_received", 0)) + 1
            except ValueError:
                print(f"⚠️ Cannot convert replies_received '{metrics.get('replies_received')}' to int.")
                updated_count = 1

            campaign_id = metrics.get("campaign_id")
            if not campaign_id:
                print("⚠️ campaign_id is missing in metrics record.")
            else:
                db_manager.update_single_field(
                    "metrics",
                    column_name="replies_received",
                    column_value=str(updated_count),
                    primary_key_col="campaign_id",
                    primary_key_value=campaign_id
                )
                print("🔄 Metrics record updated.")
        else:
            print("⚠️ No metrics record found for update.")
        dashboard_inbox_lead_records = db_manager.get_records_with_filter("email_response_guideline", lead_cols, lead_values, limit=10)
        inbox_record = {
            "campaign_id": data["Campaign ID"],
            "email": data["Lead Email"],
            "campaign_name": data.get("Campaign Name"),
            "client_id": client_details.get("client_id"),
            "full_name": lead_records.get("name"),
            "photo_url": lead_records.get("photo_url"),
            "sentiment": sentiment,
            "message" : formated_reply
            
            
        }

        if dashboard_inbox_lead_records:
            # Update existing record
            db_manager.update_multiple_fields("email_response_guideline", inbox_record, "email")
            print("🔄 Existing record updated in email_response_guideline.")
        else:
            # Insert new record
            db_manager.insert_data("email_response_guideline", inbox_record)
            print("🆕 New record inserted into email_response_guideline.")
              
        
    except Exception as e:
        print(f"❌ Error during DB test: {e}")
        raise 