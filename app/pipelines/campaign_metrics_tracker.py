import asyncio
import nest_asyncio
from apify_client import ApifyClient, ApifyClientAsync
nest_asyncio.apply()
from pyairtable import Table,Api
from datetime import datetime
import ast
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, APIFY_API_TOKEN
from db.db_utils import export_to_airtable

def unique_key_check_airtable(column_name,unique_value,table_name):
    try:
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, table_name)
        records = airtable_obj.all()
        return any(record['fields'].get(column_name) == unique_value for record in records) 
    except Exception as e:
        print(f"Error occured in {__name__} while performing unique value check in airtable. {e}")

def unique_key_check_airtable_v3(column_name1, unique_value1, column_name2, unique_value2, table_name):
    try:
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, table_name)
        records = airtable_obj.all()

        return any(
            record['fields'].get(column_name1) == unique_value1 and
            record['fields'].get(column_name2) == unique_value2
            for record in records
        )
    except Exception as e:
        print(f"Error occurred in {__name__} while performing unique value check in Airtable. {e}")
        return False

def retrieve_column_value(table_name,primary_key_col,primary_key_value,column_name):
    try:
        
        print(f'Fetching {column_name} for {primary_key_col} -> {primary_key_value}')
        api = Api(AIRTABLE_API_KEY) 
        airtable_obj = api.table(AIRTABLE_BASE_ID, table_name)
        record_details = airtable_obj.all(
          formula=f"{{{primary_key_col}}} = '{primary_key_value}'"
        )
        sorted_records = sorted(
          record_details,
          key=lambda r: r['fields'].get('created_time', ''),
          reverse=True
        )
        records_count = len(record_details)
        if records_count <1:
            print(f"No records found for the corresponding {primary_key_col} {primary_key_value} in {table_name}")
            return None
        record_details = record_details[0]
        column_value = record_details.get('fields').get(column_name,"Not available")
        print(column_value)
        return column_value
    except Exception as e:
        print(f"Error occured in {__name__} while fetching client specific column details. {e}")
        return None
       
    
def update_campaign_metrics_v3(campaign_id,instagram_username,posts_count,hashtags_required):
    try:
        profile_url = f"https://www.instagram.com/{instagram_username}/"
        created_time = retrieve_column_value(table_name="campaign_metrics_v3",primary_key_col="profile_url",primary_key_value=profile_url,column_name="created_time")
        print(f"Created time: {created_time}")

        if created_time is None:
            formatted_date = datetime.now().date().isoformat()
        else:
            dt = datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            date = dt.date()  # datetime.date(2025, 7, 24)
            date_str = str(date)  # "2025-07-24"
            formatted_date = date_str

        formatted_date = "2025-05-01"

        print(f"Formatted date: {formatted_date}")
        input_object_posts = {
            "onlyPostsNewerThan": formatted_date,
            "resultsLimit": posts_count,
            "skipPinnedPosts": True,
            "username": [instagram_username]
        }

        client = ApifyClient(token=APIFY_API_TOKEN)

        async def run_apify_actor(input_object, actor_name):
                client_async = ApifyClientAsync(APIFY_API_TOKEN)
                run = await client_async.actor(f"apify/{actor_name}").call(run_input=input_object)
                print("Actor run finished:", run)
                return run

        result_posts = asyncio.get_event_loop().run_until_complete(
            run_apify_actor(input_object_posts, "instagram-post-scraper")
        )

        print(f"Scraper Completed execution")

        dataset_id_posts = result_posts.get("defaultDatasetId")
        dataset_client_posts = client.dataset(dataset_id_posts)
        items_posts = dataset_client_posts.list_items().items 

        print(f"Dataset ID: {dataset_id_posts}")
        print(f"Items in dataset: {len(items_posts)}")

        if items_posts[0].get("error") == "no_items":
            print("No Items")

        for item in items_posts:
            print(item)
            hashtags = item.get("hashtags","")
            print(type(hashtags))
            print(f"hashtags : {hashtags}")
            if not (set(h.lower() for h in hashtags) & set(h.lower() for h in hashtags_required)):
                print("Skipping entry since no matching hashtags found")
                continue
            print(f"Matching hashtags found")
            
            data = {
                "campaign_id":campaign_id,
                "profile_url": profile_url,
                "username": instagram_username,
                "captions": str(item.get("caption", "")),
                "hashtags": str(item.get("hashtags", "")),
                "mentions": str(item.get("mentions", "")),
                "post_url": str(item.get("url", "")),
                "first_comment": str(item.get("firstComment", "")),
                "latest_comments": str(item.get("latestComments", "")),
                "display_url": str(item.get("displayUrl", "")),
                "images": str(item.get("images", "")),
                "likes_count": str(item.get("likesCount", "")),
                "comments_count": str(item.get("commentsCount", "")),
                "video_play_count": str(item.get("videoPlayCount", "")),
                "timestamp": str(item.get("timestamp", "")),
                "is_sponsored": str(item.get("isSponsored", "")),
                "comments_disabled": str(item.get("isCommentsDisabled", ""))
            }
            record_exists = unique_key_check_airtable_v3('campaign_id', campaign_id,'post_url',data["post_url"],"campaign_metrics_v3")
            # record_exists = unique_key_check_airtable('post_url',data["post_url"],"campaign_metrics_v3")
            if not record_exists:
                print(f"Record doesn't exist")
                export_to_airtable(data,"campaign_metrics_v3")
            print("\n")
        
        return True
    
    except Exception as e:
        print(f"Error occured in {__name__} while updating campaign metrics. {e}")
        return False

# if __name__ == "__main__":
#     posts_count = 5
#     campaign_id = "motorcycles"
#     instagram_username = "dqsalmaan"
#     hashtags_required = ["ULtraviolette"]
    # print(update_campaign_metrics(campaign_id,instagram_username,posts_count,hashtags_required))