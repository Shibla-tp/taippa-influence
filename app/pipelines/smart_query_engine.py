# import torch
import os
# from transformers import AutoModelForCausalLM, AutoTokenizer
import time
import openai
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,PERPLEXITY_API_KEY

def convert_text_to_sql_v2(query_text):
    try:

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        schema_context = """"

        Database schema with column descriptions:
        Table: src_influencer_data (
        id                          character varying(100000) -- Unique identifier for the influencer
        instagram_url               character varying(100000) -- URL of the influencer's Instagram profile
        instagram_followers_count   character varying(100000) -- Number of followers on Instagram
        instagram_username          character varying(100000) -- Instagram username/handle
        instagram_bio               character varying(100000) -- Bio text from the Instagram profile
        influencer_type             character varying(100000) -- Type/category of influencer (fixed category values among this: [food_vlogger,fashion_vlogger,real_estate_influencers,business_vloggers,finance_vloggers,real_estate_influencers,beauty_vlogger,tech_vloggers])
        influencer_location         character varying(100000) -- Location of the influencer
        instagram_post_urls         character varying(100000) -- List of URLs to the influencer's Instagram posts
        business_category_name      character varying(100000) -- Main business category of the influencer (Tag provided by Instagram for Business profile Eg: "Personal blog","Digital creator","Reel creator" etc)
        full_name                   character varying(100000) -- Full name of the influencer
        instagram_follows_count     character varying(100000) -- Number of accounts the influencer follows
        created_time                character varying(100000) -- Timestamp when the influencer was added to the database
        instagram_hashtags          character varying(100000) -- Hashtags used by the influencer for different posts (stored as list of strings)
        instagram_captions          character varying(100000) -- Captions from the influencer's posts (stored as list of strings)
        instagram_video_play_counts character varying(100000) -- Number of plays for video posts (stored as list of strings)
        instagram_likes_counts      character varying(100000) -- Number of likes on posts (stored as list of strings)
        instagram_comments_counts   character varying(100000) -- Number of comments on posts (stored as list of strings)
        instagram_video_urls        character varying(100000) -- URLs of video posts
        instagram_posts_count       character varying(100000) -- Total number of posts by the influencer
        external_urls               character varying(100000) -- List of external links provided by the influencer
        instagram_profile_pic       character varying(100000) -- URL of the influencer's profile picture
        influencer_nationality      character varying(100000) -- Nationality of the influencer (Include country names)
        targeted_audience           character varying(100000) -- Target audience group for the influencer (fixed category values among this: ["gen-z","gen-y", "gen-x"])
        targeted_domain             character varying(100000) -- Domain or industry targeted by the influencer (fixed categoru values among this: ["food", "fashion", "fitness", "gaming", "education", "automotive", "finance", "art"])
        profile_type                character varying(100000) -- Type of profile (fixed category values among this: ["person","group"])
        email_id                    character varying(100000) -- Email address of the influencer (if not available value is "NA")
        twitter_url                 character varying(100000) -- URL of the influencer's Twitter profile
        snapchat_url                character varying(100000) -- URL of the influencer's Snapchat profile
        phone                       character varying(100000) -- Phone number of the influencer ( if not available value is "NA")
        linkedin_url                character varying(100000) -- URL of the influencer's LinkedIn profile
        tiktok_url                  character varying(100000) -- URL of the influencer's TikTok profile
        )
        """

        # Construct the prompt
        user_prompt = f"""
        {schema_context}

        Question: {query_text}

        SQL:
        """

        # system_prompt = """
        #     You are a helpful assistant that converts natural language into SQL queries.
        #     You must always generate an SQL query on the table `src_influencer_data`.

        #     - In the SELECT clause, **return only** the following columns (nothing else):
        #     instagram_url, instagram_followers_count, influencer_type, influencer_location,
        #     business_category_name, targeted_audience, targeted_domain, profile_type

        #     - In the WHERE clause or other conditions, you are allowed to use **any other columns** from the table (e.g., instagram_bio, instagram_hashtags, etc.)

        #     - Always limit the result to a **maximum of 3 records** using `LIMIT 3`.

        #     - Do not return explanations, markdown, or SQL tags like ```sql.

        #     Example:
        #     SELECT instagram_url, instagram_followers_count, influencer_type, influencer_location,
        #         business_category_name, targeted_audience, targeted_domain, profile_type
        #     FROM src_influencer_data
        #     WHERE instagram_followers_count::int > 10000
        #     LIMIT 3;
        # """

        system_prompt = """
        You are a helpful assistant that converts natural language into SQL queries.
        You must always generate an SQL query on the table `src_influencer_data`.

        - In the SELECT clause, always use `SELECT *` to return all columns from the table.

        - In the WHERE clause or other conditions, you are allowed to use any columns from the table (e.g., instagram_bio, instagram_hashtags, etc.)

        - Always limit the result to a maximum of 3 records using `LIMIT 3`.

        - Do not return explanations, markdown, or SQL tags like ```sql.

        Example:
        SELECT *
        FROM src_influencer_data
        WHERE instagram_followers_count::int > 10000
        LIMIT 3;
        """

        # Call the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        sql_query = response.choices[0].message.content

        # Add LIMIT 3 if it's not already present
        if "limit" not in sql_query.lower():
            if ";" in sql_query:
                sql_query = sql_query.rstrip(";") + " LIMIT 3;"
            else:
                sql_query += " LIMIT 3;"

        print("Generated SQL Query:")
        print(sql_query)
    
    except Exception as e:
        print(f"Error during SQL generation: {e}")
        sql_query = None
    return sql_query


if __name__ == "__main__":
    # Example usage
    query_text = "What are the Instagram URLs of influencers with more than 10000 followers?"
    sql_query = convert_text_to_sql_v2(query_text)
    if sql_query:
        print(f"Generated SQL Query: {sql_query}")
    else:
        print("Failed to generate SQL query.")