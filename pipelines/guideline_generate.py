import openai
# from openai import OpenAI
import requests
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,PERPLEXITY_API_KEY
import pinecone
# from openai import OpenAI
import json
from ai_modules.agents_guideline import generator_guideline
from db.db_utils import retrieve_record,fetch_client_details,parse_people_info,unique_key_check_airtable,export_to_airtable,retrieve_client_tables,fetch_client_outreach_mappings,fetch_client_column
from db.db_ops import db_manager

openai.api_key = OPENAI_API_KEY

def execute_generate_sequence():
    try:
        # Listing all the records with Inactive status
        lead_info = db_manager.get_record("outreach_guideline","status","Inactive")
        generator_guideline.lead_info = lead_info

        print(f"\n-------------------------Lead info--------------------------------\n {generator_guideline.lead_info}\n")
        generator_guideline.industry_type = generator_guideline.classify_company_vertical()
        print(f"\n-------------------------Industry type--------------------------------\n {generator_guideline.industry_type}\n")
        generator_guideline.person_research_data = generator_guideline.get_recent_achievements_person()
        print(f"\n------------------------ Person research data --------------------------------\n {generator_guideline.person_research_data}\n")
        generator_guideline.company_research_data = generator_guideline.get_recent_achievements_company()
        print(f"\n------------------------ Company research data ---------------------------------\n {generator_guideline.company_research_data}\n")
        generator_guideline.company_competitors = generator_guideline.get_competitors_company()
        print(f"\n------------------------ Company Competitors ---------------------------------\n {generator_guideline.company_competitors}\n")

        if generator_guideline.industry_type in ["advertising_agencies"]:
            generator_guideline.search_term_cvp = generator_guideline.generate_search_term_cvp_agencies()
        else:
            generator_guideline.search_term_cvp = generator_guideline.generate_search_term_cvp_brands_media()
        
        print(f"\n---------------------- Client Value Proposition Search Term ----------------------------------\n {generator_guideline.search_term_cvp}\n")
        query_vector_cvp = generator_guideline.create_embedding_from_response_text(generator_guideline.search_term_cvp)
        # print(query_vector_cvp)
        cvp_search_result_json = generator_guideline.query_top_k_from_pinecone(
            query_vector=query_vector_cvp,
            top_k=10,
            namespace="",
            include_metadata=True)
        
        if generator_guideline.industry_type in ["advertising_agencies"]:
            generator_guideline.cvp = generator_guideline.generate_cvp_agencies(cvp_search_result_json)
        else:
            generator_guideline.cvp = generator_guideline.generate_cvp_brands_media(cvp_search_result_json)

        print(f"\n---------------------- Client Value Proposition ----------------------------------\n {generator_guideline.cvp}\n")
        generator_guideline.search_term_pain_points = generator_guideline.generate_customer_pain_point_term()
        print(f"\n---------------------- Client Pain Points Search Term ----------------------------------\n {generator_guideline.search_term_pain_points}\n")
        query_vector_pain_points = generator_guideline.create_embedding_from_response_text(generator_guideline.search_term_pain_points)
        # print(query_vector_pain_points)
        pain_points_search_result_json = generator_guideline.query_top_k_from_pinecone(
            query_vector=query_vector_pain_points,
            top_k=10,
            namespace="",
            include_metadata=True)

        generator_guideline.pain_points = generator_guideline.generate_pain_points(pain_points_search_result_json)
        print(f"\n---------------------- Client Pain Points ----------------------------------\n {generator_guideline.pain_points}\n")
        generator_guideline.b2b_sales_content = generator_guideline.generate_b2b_sales_email()
        print(f"\n---------------------- B2B Sales Content ----------------------------------\n {generator_guideline.b2b_sales_content}\n")
        generator_guideline.linkedin_message_content = generator_guideline.optimize_linkedin_outreach_message()
        print(f"\n---------------------- LinkedIn Message Content ----------------------------------\n {generator_guideline.linkedin_message_content}\n")
        generator_guideline.follow_up_email_content= generator_guideline.generate_follow_up_email_sections()
        print(f"\n---------------------- Follow-Up Email Content ----------------------------------\n {generator_guideline.follow_up_email_content}\n")
        generator_guideline.follow_up_linkedin_message_content = generator_guideline.generate_follow_up_linkedin_message_sections()
        print(f"\n---------------------- Follow-Up LinkedIn Message Content ----------------------------------\n {generator_guideline.follow_up_linkedin_message_content}\n")
        generator_guideline.linkedin_connection_message_content = generator_guideline.generate_linkedin_connection_message_sections()
        print(f"\n---------------------- LinkedIn Connection Message Content ----------------------------------\n {generator_guideline.follow_up_linkedin_message_content}\n")
        generator_guideline.linkedin_connection_message = generator_guideline.generate_linkedin_connection_message()
        print(f"\n---------------------- LinkedIn Connection Message  ----------------------------------\n {generator_guideline.linkedin_connection_message}\n")
        
        email_1 = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Guideline Email</title>
        </head>
        <body>
            <p>
                Hi {generator_guideline.lead_info.get('recipient_first_name')},<br><br>
                {generator_guideline.b2b_sales_content.get('ice_breaker',"")}
            <br><br>
                {generator_guideline.b2b_sales_content.get('client_value_proposition',"")}
            <br><br>
                {generator_guideline.b2b_sales_content.get('case_studies',"")} 
            <br><br>
                {generator_guideline.b2b_sales_content.get('call_to_action',"")}
            <br><br>
        Best,<br>
        Team Guideline<br>
        </p>
        </body>
        </html>
        """

        email_2 = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Guideline Email</title>
        </head>
        <body>
            <p>
                Hi {generator_guideline.lead_info.get('recipient_first_name')},<br><br>
                {generator_guideline.follow_up_email_content.get('ice_breaker_follow_up',"")}
            <br><br>
                {generator_guideline.follow_up_email_content.get('about_company_follow_up',"")}
            <br><br>
                {generator_guideline.follow_up_email_content.get('call_to_action_follow_up',"")} 
            <br><br>
        Best,<br>
        Team Guideline<br>
        </p>
        </body>
        </html>
        """

        linkedin_message = f"""Hi {generator_guideline.lead_info.get('recipient_first_name',"")},

        {generator_guideline.linkedin_message_content.get('ice_breaker_linkedin',"")}

        {generator_guideline.linkedin_message_content.get('about_company_linkedin',"")}

        {generator_guideline.linkedin_message_content.get('call_to_action_linkedin',"")}

        Best,
        Team Guideline
        """

        linkedin_message_follow_up = f"""Hi {generator_guideline.lead_info.get('recipient_first_name')},

        {generator_guideline.follow_up_linkedin_message_content.get('ice_breaker_linkedin_follow_up',"")}

        {generator_guideline.follow_up_linkedin_message_content.get('about_company_linkedin_follow_up',"")}

        {generator_guideline.follow_up_linkedin_message_content.get('call_to_action_linkedin_follow_up',"")}

        Best,
        Team Guideline
        """

        linkedin_connection_message = generator_guideline.linkedin_connection_message

        print(f"\n---------------------- Email ----------------------------------\n {email_1}\n")
        print(f"\n---------------------- Email Follow Up ----------------------------------\n {email_2}\n")
        print(f"\n---------------------- LinkedIn Message ----------------------------------\n {linkedin_message}\n")
        print(f"\n---------------------- LinkedIn Message Follow Up ----------------------------------\n {linkedin_message_follow_up}\n")
        print(f"\n---------------------- LinkedIn Connection Message ----------------------------------\n {linkedin_connection_message}\n")
        update_fields = {
            "apollo_id": generator_guideline.lead_info.get("apollo_id"),
            "industry_sector":generator_guideline.industry_type,
            "linkedin_message": linkedin_message,
            "linkedin_message_2": linkedin_message_follow_up,
            "email_message": email_1,
            "email_message_2": email_2,
            "linkedin_connection_message": linkedin_connection_message,
            "status": "Approved"
        }
        db_manager.update_multiple_fields("outreach_guideline", update_fields, "apollo_id")
        print(f"Outreach guideline table updated successfully with the generated content")
        generate_status = {
            "status":"Success",
            "message":"Successfully generated the outreach content",
            "updated_fields": update_fields
        }
        # Send the generated contnet to the client
    except Exception as e:
        print(f"Error occured at {__name__} while executing the generate sequence: {e}")
        generate_status = {
            "status":"Error",
            "message":f"Error occured while executing the generate sequence: {e}",
            "updated_fields": {}
        }
    return generate_status