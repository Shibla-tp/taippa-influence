from db.db_ops import db_manager

def linkedin_invite_sent_tracker(data):
    try:
        # data = {
        #     "thread_id": "influencer_marketing_60d2165a8530680001f38bd7",
        #     "campaign_name": "influencer_marketing",
        #     "linkedin_profile_url": "http://www.linkedin.com/in/carlybrower",
        #     "full_name": "Magda Houalla",
        #     "email": "magdaoualla@gmail.com",
        #     "picture": "https://media.licdn.com/dms/image/v2/D5603AQHeEZ4rcWOAXg/profile-displayphoto-shrink_200_200/profile-displayphoto-shrink_200_200/0/1728920716356?e=1750291200&v=beta&t=Xhuu3diZgNeydUQs0OE2zPQOwH5L3321gUHQVYSuwBo",
            
        # }

        table_name = "leadsin_invite_sent_linkedin"

        # Insert data
        db_manager.insert_data(table_name, data)

        # Search in first table
        cols_list = ['campaign_name', 'linkedin_profile_url']
        
        col_values = [data["campaign_name"], data["linkedin_profile_url"]]
 
        print(f"✅ Data inserted successfully to: {table_name}")

        # Now check linkedin_leads table
        leadsrecords = db_manager.get_records_with_filter("linkedin_leads", cols_list, col_values, limit=1)
        if isinstance(leadsrecords, dict):
            leadsrecords = [leadsrecords]
        print(f"🔢 Matching Record Count in linkedin_leads: {len(leadsrecords)}")

        if len(leadsrecords) == 1:
            print("🛠 Only one matching record found in linkedin_leads. Updating status to LinkedIn Invite Sent.")
            record = leadsrecords[0]
            db_manager.update_single_field(
                table_name="linkedin_leads",
                column_name='status',
                column_value='LinkedIn Invite Sent',
                primary_key_col='thread_id',
                primary_key_value=record['thread_id']
            )
            print(f"✅ Record updated status to 'LinkedIn Invite Sent' successfully.")


    except Exception as e:
        print(f"❌ Error during DB test: {e}")
        raise
