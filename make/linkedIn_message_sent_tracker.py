from db.db_ops import db_manager

def linkedin_message_sent_tracker(data):
    try:
        # data = {
        #     "thread_id": "influencer_marketing_60d2165a8530680001f38bd8",
        #     "campaign_name": "influencer_marketing",
        #     "linkedin_profile_url": "http://www.linkedin.com/in/pj-leimgruber",
        #     "full_name": "Magda Houalla",
        #     "email": "magdaoualla@gmail.com",
        #     "picture": "https://media.licdn.com/dms/image/v2/D5603AQHeEZ4rcWOAXg/profile-displayphoto-shrink_200_200/profile-displayphoto-shrink_200_200/0/1728920716356?e=1750291200&v=beta&t=Xhuu3diZgNeydUQs0OE2zPQOwH5L3321gUHQVYSuwBo"
        # }

        table_name = "leadsin_message_sent_linkedin"

        # Insert data
        # db_manager.insert_data(table_name, data)

        # Search in first table
        cols_list = ['campaign_name', 'linkedin_profile_url']
        col_values = [data["campaign_name"], data["linkedin_profile_url"]]
        result = db_manager.get_records_with_filter(table_name, cols_list, col_values, limit=1)

        # Ensure result is a list
        if isinstance(result, dict):
            result = [result]

        print(f"🔢 Search result: {result}")
        # print(f"🔢 Matching Record Count in {table_name}: {len(result)}")
        if result is None:
            record_status = "First LinkedIn Message Sent"
        else:
            record_status = "Follow-up Message Sent"


        # Now check linkedin_leads table
        leadsrecords = db_manager.get_records_with_filter("linkedin_leads", cols_list, col_values, limit=1)
        if isinstance(leadsrecords, dict):
            leadsrecords = [leadsrecords]
        print(f"🔢 Matching Record Count in linkedin_leads: {len(leadsrecords)}")

        if len(leadsrecords) == 1:
            print(f"🛠 Only one matching record found in linkedin_leads. Updating status to {record_status}.")
            if leadsrecords:
                record = leadsrecords[0]  # Pick the first one if available
                db_manager.update_single_field(
                    table_name="linkedin_leads",
                    column_name='status',
                    column_value=record_status,
                    primary_key_col='thread_id',
                    primary_key_value=record['thread_id']
                )
                print(f"✅ Record updated status to {record_status} successfully.")
            else:
                print("⚠ No record found in linkedin_leads to update.")
        
        db_manager.insert_data(table_name, data)
        print("Completed linkedin message sent updation")
    except Exception as e:
        print(f"❌ Error during DB test: {e}")
        raise