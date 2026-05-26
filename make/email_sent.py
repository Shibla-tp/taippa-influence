from db.db_ops import db_manager 

def email_sent_tracker(data):
    try:
        # data = {
        #     "Campaign ID": "8f863581-3c23-4e7b-ba28-f078afaf4578",
        #     "Lead Email": "katie.hiatt@aspireiq.com",
        #     "Campaign Name": "GuidelineInfluencer", 
        #     "personalization": "Hi Taylor",
        #     "FollowUpEmail" : "Hello Taylor",
        #     "step": "2", 
        # }

        # Step 1: Fetch client info using campaign ID
        cols_list = ['instantly_campaign_id']
        col_values = [data["Campaign ID"]]
        client_details = db_manager.get_records_with_filter("client_info", cols_list, col_values, limit=10)

        if not client_details:
            print("⚠️ No client found with the given campaign ID.")
            return

        print(f"🔢 Client Details: {client_details}")

        cleaned_table = client_details.get("cleaned_table")
        outreach_table = client_details.get("outreach_table")
        if not cleaned_table:
            print("⚠️ 'cleaned_table' key not found in client details.")
            return

        print(f"✅ Cleaned Table: {cleaned_table}")
        print(f"✅ Outreach Table: {outreach_table}")
        

        # Step 2: Fetch lead info using email
        lead_cols = ['email']
        lead_values = [data["Lead Email"]]
        lead_records = db_manager.get_records_with_filter(cleaned_table, lead_cols, lead_values, limit=10)
        # print(f"Lead Records: {lead_records}")
        # if lead_records:
        #     print(f"✅ Lead found in cleaned_table: {lead_records[0]}")
        # else:
        #     print("⚠️ No lead found with the given email in the cleaned_table.")

        # # Step 3: Check dashboard_inbox table
        # dashboard_inbox_lead_cols = ['email']
        # dashboard_inbox_lead_values = [data["Lead Email"]]
        dashboard_inbox_lead_records = db_manager.get_records_with_filter("dashboard_inbox", lead_cols, lead_values, limit=10)
        # print(f"\n\nDashboard inbox Records: {dashboard_inbox_lead_records}")
        # if dashboard_inbox_lead_records:
        #     print(f"✅ Lead found in dashboard_inbox table: {dashboard_inbox_lead_records[0]}")
        # else:
        #     print("⚠️ No lead found with the given email in the dashboard_inbox table.")

        inbox_record = {
            "campaign_id": data["Campaign ID"],
            "client_id": client_details.get("client_id"),
            "email": data["Lead Email"],
            "name": lead_records.get("name"),
            "profile_picture_url": lead_records.get("photo_url"),
            "email_step": data.get("step"),
            "email_1_content": data.get("personalization"),
            "email_2_content": data.get("FollowUpEmail"),
            "campaign_name": data.get("Campaign Name"),
            "whatspp_campaign_name": "Taippa",
            "whatsappbotid":"15557054487",
        }

        if dashboard_inbox_lead_records:
            # Update existing record
            db_manager.update_multiple_fields("dashboard_inbox", inbox_record, "email")
            print("🔄 Existing record updated in dashboard_inbox.")
        else:
            # Insert new record
            db_manager.insert_data("dashboard_inbox", inbox_record)
            print("🆕 New record inserted into dashboard_inbox.")

        outreach_records = db_manager.get_records_with_filter(
            outreach_table, ["recipient_email"], [data["Lead Email"]], limit=10
        )
        # outreach = outreach_records[0] if outreach_records else {}

        if outreach_records:
            db_manager.update_single_field(
                outreach_table,
                column_name="email_step",
                column_value=data["step"],
                primary_key_col="apollo_id",
                primary_key_value=outreach_records.get("apollo_id")
            )
            print("🔄 Outreach record updated.")
        else:
            print("⚠️ No outreach record found for update.")
        metrics_records = db_manager.get_records_with_filter(
            "metrics", ["campaign_id"], [data["Campaign ID"]], limit=10
        )
        if metrics_records:
            print(f"Metrics Record: {metrics_records}")
            metrics = metrics_records  # Fix: No need to index

            try:
                updated_count = int(metrics.get("sequence_started", 0)) + 1
            except ValueError:
                print(f"⚠️ Cannot convert sequence_started '{metrics.get('sequence_started')}' to int.")
                updated_count = 1

            campaign_id = metrics.get("campaign_id")
            if not campaign_id:
                print("⚠️ campaign_id is missing in metrics record.")
            else:
                db_manager.update_single_field(
                    "metrics",
                    column_name="sequence_started",
                    column_value=str(updated_count),
                    primary_key_col="campaign_id",
                    primary_key_value=campaign_id
                )
                print("🔄 Metrics record updated.")
        else:
            print("⚠️ No metrics record found for update.")

        
        
    except Exception as e:
        print(f"❌ Error during DB test: {e}")
        raise 