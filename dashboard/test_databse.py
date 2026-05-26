from db.db_ops import db_manager

def run_database_test():
    try:
        data = {
            "thread_id": "influencer_marketing_60d2165a8530680001f38bd7",
            "campaign_name": "influencer_marketing",
            "linkedin_profile_url": "http://www.linkedin.com/in/carlybrower",
            "full_name": "Magda Houalla",
            "email": "magdaoualla@gmail.com",
            "picture": "https://media.licdn.com/dms/image/v2/D5603AQHeEZ4rcWOAXg/profile-displayphoto-shrink_200_200/profile-displayphoto-shrink_200_200/0/1728920716356?e=1750291200&v=beta&t=Xhuu3diZgNeydUQs0OE2zPQOwH5L3321gUHQVYSuwBo"
        }

        table_name = "leadsin_message_sent_linkedin"

        # Insert data
        db_manager.insert_data(table_name, data)

        # Search in first table
        cols_list = ['campaign_name', 'linkedin_profile_url']
        col_values = ['influencer_marketing', 'http://www.linkedin.com/in/carlybrower']
        result = db_manager.get_record(table_name, cols_list, col_values, limit=2)

        # Ensure result is a list
        if isinstance(result, dict):
            result = [result]

        print(f"🔢 Search result: {result}")
        print(f"🔢 Matching Record Count in {table_name}: {len(result)}")

        print(f"✅ Data inserted and queried successfully from: {table_name}")

        # Now check linkedin_leads table
        leadsrecords = db_manager.get_record("linkedin_leads", cols_list, col_values, limit=1)
        if isinstance(leadsrecords, dict):
            leadsrecords = [leadsrecords]
        print(f"🔢 Matching Record Count in linkedin_leads: {len(leadsrecords)}")

        if len(leadsrecords) == 1:
            print("🛠 Only one matching record found in linkedin_leads. Updating status to Follow-up Message Sent.")
            record = leadsrecords[0]
            db_manager.update_single_field(
                table_name="linkedin_leads",
                column_name='status',
                column_value='Follow-up Message Sent',
                primary_key_col='thread_id',
                primary_key_value=record['thread_id']
            )
            print(f"✅ Record updated status to 'Follow-up Message Sent' successfully.")
        else:
            print("🛠 Zero or multiple matching records found in linkedin_leads. Updating status to First LinkedIn Message Sent.")
            if leadsrecords:
                record = leadsrecords[0]  # Pick the first one if available
                db_manager.update_single_field(
                    table_name="linkedin_leads",
                    column_name='status',
                    column_value='First LinkedIn Message Sent',
                    primary_key_col='thread_id',
                    primary_key_value=record['thread_id']
                )
                print(f"✅ Record updated status to 'First LinkedIn Message Sent' successfully.")
            else:
                print("⚠ No record found in linkedin_leads to update.")

    except Exception as e:
        print(f"❌ Error during DB test: {e}")
        raise
