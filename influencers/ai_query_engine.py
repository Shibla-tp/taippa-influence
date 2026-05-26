from pyairtable import Table
import openai
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS


openai_client = openai.OpenAI(api_key=OPENAI_API_KEY) 

# --- Generate filter formula from user query ---
def generate_airtable_formula(user_query,airtable_fields):

    prompt = f"""
    You are an assistant that generates Airtable filterByFormula expressions based on user queries.

    Airtable Table Schema:
    {airtable_fields}

    User Query:
    "{user_query}"

    Return only the Airtable formula, with no explanation or markdown.
    """

    response = openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )

    formula = response.choices[0].message.content.strip()
    # Remove code block formatting if present
    if formula.startswith("```"):
        formula = formula.split("```")[1].strip()
    return formula

# --- Fetch records from Airtable ---
def fetch_records_from_airtable(table, filter_formula):
    try:
        records = table.all(formula=filter_formula,max_records=3)
        return records
    except Exception as e:
        print(f"❌ Error fetching records: {e}")
        return []

def airtable_formula_generator(influencer_table,user_query):
    """
    Query Airtable with the given filter formula and return the records.
    """
    try:
        airtable_fields = """
        Database schema with column descriptions:
            Table: src_influencer_data (
            id                          long text -- Unique identifier for the influencer
            instagram_url               long text -- URL of the influencer's Instagram profile (if null it would have values as '', 'NA','N/A')
            instagram_followers_count   Long text -- Number of followers on Instagram
            instagram_username          Long text -- Instagram username/handle
            instagram_bio               Long text -- Bio text from the Instagram profile
            influencer_type             Long text -- Type/category of influencer (fixed category values among this: [food_vlogger,fashion_vlogger,real_estate_influencers,business_vloggers,finance_vloggers,real_estate_influencers,beauty_vlogger,tech_vloggers])
            influencer_location         Long text -- Location of the influencer
            instagram_post_urls         Long text -- List of URLs to the influencer's Instagram posts
            business_category_name      Long text -- Main business category of the influencer (Tag provided by Instagram for Business profile Eg: "Personal blog","Digital creator","Reel creator" etc)
            full_name                   Long text -- Full name of the influencer
            instagram_follows_count     Long text -- Number of accounts the influencer follows
            created_time                Long text -- Timestamp when the influencer was added to the database
            instagram_hashtags          Long text -- Hashtags used by the influencer for different posts (stored as list of strings)
            instagram_captions          Long text -- Captions from the influencer's posts (stored as list of strings)
            instagram_video_play_counts Long text -- Number of plays for video posts (stored as list of strings)
            instagram_likes_counts      Long text -- Number of likes on posts (stored as list of strings)
            instagram_comments_counts   Long text -- Number of comments on posts (stored as list of strings)
            instagram_video_urls        Long text -- URLs of video posts
            instagram_posts_count       Long text -- Total number of posts by the influencer
            external_urls               Long text -- List of external links provided by the influencer
            instagram_profile_pic       Long text -- URL of the influencer's profile picture
            influencer_nationality      Long text -- Nationality of the influencer (Include country names)
            targeted_audience           Long text -- Target audience group for the influencer (fixed category values among this: ["gen-z","gen-y", "gen-x"])
            targeted_domain             Long text -- Domain or industry targeted by the influencer (fixed categoru values among this: ["food", "fashion", "fitness", "gaming", "education", "automotive", "finance", "art"])
            profile_type                Long text -- Type of profile (fixed category values among this: ["person","group"])
            email_id                    Long text -- Email address of the influencer (if not available value is "NA")
            twitter_url                 Long text -- URL of the influencer's Twitter profile
            snapchat_url                Long text -- URL of the influencer's Snapchat profile
            phone                       Long text -- Phone number of the influencer ( if not available value is "NA")
            linkedin_url                Long text -- URL of the influencer's LinkedIn profile
            tiktok_url                  Long text -- URL of the influencer's TikTok profile
            )
        """
        table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, influencer_table)
        # Step 3: Generate formula
        formula = generate_airtable_formula(user_query,airtable_fields)
        print(f"\n🧠 Generated Formula:\n{formula}\n")
        return formula
    except Exception as e:
        print(f"Error generating formula: {e}")
        return []

def fetch_records_from_airtable_with_formula(table, formula):
    """
    Fetch records from Airtable using the provided filter formula.
    """
    try:
        airtable = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, table)
        records = airtable.all(formula=formula, max_records=3)
        if not records:
            print("⚠️ No matching records found.")
        else:
            print(f"✅ Found {len(records)} record(s):")
            for i, record in enumerate(records, 1):
                print(f"\n🔹 Record {i}")
                for key, value in record["fields"].items():
                    print(f"  {key}: {value}")
        return records
    except Exception as e:
        print(f"❌ Error fetching records: {e}")
        return []

