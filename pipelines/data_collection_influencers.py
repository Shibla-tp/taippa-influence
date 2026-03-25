import asyncio
import nest_asyncio
from apify_client import ApifyClient, ApifyClientAsync
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS,APIFY_API_TOKEN
from pyairtable import Table,Api
from db.db_ops import db_manager
nest_asyncio.apply()

client = ApifyClient(token=APIFY_API_TOKEN)

# -----------------------------
# Utility Functions
# -----------------------------

def safe_str(value):
    return str(value).strip() if value else ""

def safe_int(value):
    try:
        return int(value)
    except:
        return 0

def safe_float(value):
    try:
        return float(value)
    except:
        return 0.0


# -----------------------------
# Instagram PRO Scraper
# -----------------------------

async def profile_scraper(usernames: list):
    try:
        run = await client_async.actor(
            "powerful_bachelor/instagram-profile-scraper-pro"
        ).call(run_input={"usernames": usernames})

        dataset_id = run.get("defaultDatasetId")
        dataset_client = client_async.dataset(dataset_id)

        dataset_items_response = await dataset_client.list_items()
        items = dataset_items_response.items

        results = []

        for item in items:
            engagement_rate_raw = safe_float(item.get("engagement_rate", 0))

            # Convert to percentage if needed (PRO usually returns 0.05 style values)
            engagement_percentage = round(engagement_rate_raw * 100, 2)

            results.append({
                "instagram_url": safe_str(
                    item.get("url") 
                    or item.get("inputUrl") 
                    or f"https://instagram.com/{item.get('username')}"
                ),
                "instagram_username": safe_str(item.get("username")),
                "full_name": safe_str(item.get("full_name") or item.get("fullName")),
                "instagram_bio": safe_str(item.get("biography")),
                "external_urls": safe_str(item.get("externalUrls") or item.get("externalUrl")),
                "instagram_followers_count": safe_int(item.get("followers_count") or item.get("followersCount")),
                "instagram_follows_count": safe_int(item.get("follows_count") or item.get("followsCount")),
                "business_category_name": safe_str(item.get("business_category_name") or item.get("businessCategoryName")),
                "instagram_profile_pic": safe_str(item.get("profile_pic_hd") or item.get("profilePicUrl")),
                "instagram_posts_count": safe_int(item.get("posts_count") or item.get("postsCount")),

                # Engagement Metrics
                "engagement_rate_percent": engagement_percentage,
                "average_likes": safe_float(item.get("average_likes")),
                "average_comments": safe_float(item.get("average_comments")),
                "average_views": safe_float(item.get("average_views")),
            })

        return results

    except Exception as e:
        print(f"❌ Error fetching Instagram data: {e}")
        return []
    
# def safe_int(value):
#     try:
#         return int(value) if value is not None else 0
#     except:
#         return 0

# def safe_str(value):
#     if value is None:
#         return ""
#     if isinstance(value, list):
#         # join list of dicts or strings
#         new_list = []
#         for v in value:
#             if isinstance(v, dict):
#                 new_list.append(v.get("url") or v.get("lynx_url") or str(v))
#             else:
#                 new_list.append(str(v))
#         return ", ".join(new_list)
#     return str(value)

# # ------------------- Profile Scraper -------------------

# def profile_scraper(instagram_username):
#     try:
#         input_object_profile = {"usernames": [instagram_username]}

#         async def run_apify_actor(input_object, actor_name):
#             client_async = ApifyClientAsync(APIFY_API_TOKEN)
#             run = await client_async.actor(f"apify/{actor_name}").call(run_input=input_object)
#             return run
            
#         # Run the actor
#         result_profile = asyncio.get_event_loop().run_until_complete(
#             run_apify_actor(input_object_profile, "powerful_bachelor/instagram-profile-scraper-pro")
#         )
        

#         # Fetch dataset items
#         dataset_id_profile = result_profile.get("defaultDatasetId")
#         client_sync = ApifyClient(APIFY_API_TOKEN)
#         dataset_client_profile = client_sync.dataset(dataset_id_profile)
#         items_profile = dataset_client_profile.list_items().items

#         instagram_data = {}
#         if items_profile:
#             item = items_profile[0]
#             instagram_data["instagram_url"] = safe_str(item.get("url") or item.get("inputUrl"))
#             instagram_data["instagram_username"] = safe_str(item.get("username"))
#             instagram_data["full_name"] = safe_str(item.get("fullName"))
#             instagram_data["instagram_bio"] = safe_str(item.get("biography"))
#             instagram_data["external_urls"] = safe_str(item.get("externalUrls") or item.get("externalUrl"))
#             instagram_data["instagram_followers_count"] = safe_int(item.get("followersCount"))
#             instagram_data["instagram_follows_count"] = safe_int(item.get("followsCount"))
#             instagram_data["business_category_name"] = safe_str(item.get("businessCategoryName"))
#             instagram_data["instagram_profile_pic"] = safe_str(item.get("profilePicUrl"))
#             instagram_data["instagram_posts_count"] = safe_int(item.get("postsCount"))
#         else:
#             print(f"No data found for {instagram_username}")

#         # instagram_data["influencer_type"] = safe_str(influencer_type)
#         # instagram_data["influencer_location"] = safe_str(influencer_location)

#         return instagram_data

#     except Exception as e:
#         print(f"Error occured while executing the profile scraper: {e}")
#         return {}


# def profile_scraper(instagram_username,influencer_type,influencer_location):
#     try:
#         # --------------------------- Profile Scraper ---------------------------

#         input_object_profile = {"usernames": [instagram_username]}

#         async def run_apify_actor(input_object, actor_name):
#             client_async = ApifyClientAsync(APIFY_API_TOKEN)
#             run = await client_async.actor(f"apify/{actor_name}").call(run_input=input_object)
#             print("Actor run finished:", run)
#             return run

#         result_profile = asyncio.get_event_loop().run_until_complete(
#             run_apify_actor(input_object_profile, "instagram-profile-scraper")
#         )

#         dataset_id_profile = result_profile.get("defaultDatasetId")
#         dataset_client_profile = client.dataset(dataset_id_profile)
#         items_profile = dataset_client_profile.list_items().items

#         instagram_data = {}
#         for item in items_profile:
#             instagram_data["instagram_url"] = item.get("inputUrl")
#             instagram_data["instagram_username"] = item.get("username")
#             instagram_data["full_name"] = item.get("fullName")
#             instagram_data["instagram_bio"] = item.get("biography")
#             instagram_data["external_urls"] = str(item.get("externalUrls"))
#             instagram_data["instagram_followers_count"] = int(item.get("followersCount"))
#             instagram_data["instagram_follows_count"] = int(item.get("followsCount"))
#             instagram_data["business_category_name"] = str(item.get("businessCategoryName"))
#             instagram_data["instagram_profile_pic"] = str(item.get("profilePicUrl"))
#             instagram_data["instagram_posts_count"] = int(item.get("postsCount"))
#         instagram_data["influencer_type"] = str(influencer_type)
#         instagram_data["influencer_location"] = str(influencer_location)
#         # --------------------------- Post Scraper ---------------------------
#         return instagram_data
    
#     except Exception as e:
#         print(f"Error occured while executing the profile scraper: {e}")

# def post_scraper(instagram_username,posts_count,followers_count):
#     try:

#         input_object_posts = {
#             "resultsLimit": posts_count,
#             "skipPinnedPosts": False,
#             "username": [instagram_username]
#         }
        
#         async def run_apify_actor(input_object, actor_name):
#                 client_async = ApifyClientAsync(APIFY_API_TOKEN)
#                 run = await client_async.actor(f"apify/{actor_name}").call(run_input=input_object)
#                 print("Actor run finished:", run)
#                 return run
        
#         result_posts = asyncio.get_event_loop().run_until_complete(
#             run_apify_actor(input_object_posts, "instagram-post-scraper")
#         )

#         print(f"Scraper Completed execution")

#         dataset_id_posts = result_posts.get("defaultDatasetId")
#         dataset_client_posts = client.dataset(dataset_id_posts)
#         items_posts = dataset_client_posts.list_items().items 

#         print(f"Dataset ID: {dataset_id_posts}")
#         print(f"Items in dataset: {len(items_posts)}")
#         captions = []
#         hashtags = []
#         post_urls = []
#         comments_counts = []
#         video_play_counts = []
#         video_urls = []
#         likes_counts= []
#         instagram_data = {}
#         comments_count,likes_count = 0,0
#         for item in items_posts:
#             print(item)
#             caption = item.get("caption", "")
#             trimmed_caption = caption[:80]
#             captions.append(trimmed_caption)
#             hashtags.append(item.get("hashtags", ""))
#             post_urls.append(item.get("url", ""))
#             comments_counts.append(item.get("commentsCount", 0))
#             video_play_counts.append(item.get("videoPlayCount", 0))
#             video_urls.append(item.get("videoUrl", ""))
#             likes_counts.append(item.get("likesCount",0))
#             comments_count += item.get("commentsCount", 0)
#             likes_count += item.get("likesCount", 0)

#         print(f"Seggregated data from the posts")
#         instagram_data["instagram_captions"] = str(captions)
#         instagram_data["instagram_hashtags"] = str(hashtags)
#         instagram_data["instagram_post_urls"] = str(post_urls)
#         instagram_data["instagram_comments_counts"] = str(comments_counts)
#         instagram_data["instagram_video_play_counts"] = str(video_play_counts)
#         instagram_data["instagram_video_urls"] = str(video_urls)
#         instagram_data["instagram_likes_counts"] = str(likes_counts)
        
#         # Compute averages for numeric lists:
#         instagram_data["avg_comments"] = int(sum(comments_counts) / len(comments_counts)) if comments_counts else 0
#         instagram_data["avg_likes"]  = int(sum(likes_counts) / len(likes_counts)) if likes_counts else 0
#         instagram_data["avg_video_play_counts"] = int(sum(video_play_counts) / len(video_play_counts)) if video_play_counts else 0
#         total_engagements = comments_count + likes_count
#         engagement_rate = round((total_engagements / followers_count) * 100, 2) if followers_count > 0 else 0
#         estimated_reach = instagram_data["avg_video_play_counts"]
#         instagram_data["engagement_rate"] = engagement_rate
#         instagram_data["estimated_reach"] = estimated_reach
#         return instagram_data
    
#     except Exception as e:
#         print(f"Error occured while executing the post scraper: {e}")

def safe_int(value):
    try:
        return int(value) if value is not None else 0
    except:
        return 0

def post_scraper(instagram_username, posts_count, followers_count):
    try:
        input_object_posts = {
            "resultsLimit": posts_count,
            "skipPinnedPosts": False,
            "username": [instagram_username]
        }
        
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

        captions, hashtags, post_urls, comments_counts, video_play_counts, video_urls, likes_counts = ([] for _ in range(7))
        instagram_data = {}
        comments_count, likes_count = 0, 0

        for item in items_posts:
            print(item)
            caption = item.get("caption", "") or ""
            trimmed_caption = caption[:80]
            captions.append(trimmed_caption)
            hashtags.append(item.get("hashtags", "") or "")
            post_urls.append(item.get("url", "") or "")
            
            c = safe_int(item.get("commentsCount"))
            l = safe_int(item.get("likesCount"))
            v = safe_int(item.get("videoPlayCount"))

            comments_counts.append(c)
            video_play_counts.append(v)
            video_urls.append(item.get("videoUrl", "") or "")
            likes_counts.append(l)

            comments_count += c
            likes_count += l

        print(f"Seggregated data from the posts")
        instagram_data["instagram_captions"] = str(captions)
        instagram_data["instagram_hashtags"] = str(hashtags)
        instagram_data["instagram_post_urls"] = str(post_urls)
        instagram_data["instagram_comments_counts"] = str(comments_counts)
        instagram_data["instagram_video_play_counts"] = str(video_play_counts)
        instagram_data["instagram_video_urls"] = str(video_urls)
        instagram_data["instagram_likes_counts"] = str(likes_counts)
        
        # Compute averages for numeric lists:
        # instagram_data["avg_comments"] = int(sum(comments_counts) / len(comments_counts)) if comments_counts else 0
        # instagram_data["avg_likes"]  = int(sum(likes_counts) / len(likes_counts)) if likes_counts else 0
        # instagram_data["avg_video_play_counts"] = int(sum(video_play_counts) / len(video_play_counts)) if video_play_counts else 0
        
        # total_engagements = comments_count + likes_count
        # engagement_rate = round((total_engagements / followers_count) * 100, 2) if followers_count > 0 else 0
        # estimated_reach = instagram_data["avg_video_play_counts"]

        # instagram_data["engagement_rate"] = engagement_rate
        # instagram_data["estimated_reach"] = estimated_reach

        return instagram_data
    
    except Exception as e:
        print(f"Error occured while executing the post scraper: {e}")


def add_influencer_to_db(combined_influencer_data):
    try:
        record_exists = db_manager.unique_key_check('instagram_url', combined_influencer_data['instagram_url'], "src_influencer_data")
        if record_exists:
            print(f"Record with the following instagram url: {combined_influencer_data['instagram_url']} already exists. Skipping the entry...")
        db_manager.insert_data("src_influencer_data",combined_influencer_data)
        return True
    except Exception as e:
        print(f"Error occured while adding influencer data to the database: {e}")
        return False

def data_collection(instagram_username,influencer_type,influencer_location,posts_count):
    # --------------------------- Profile Scraper ---------------------------
    influencer_basic_data = profile_scraper(instagram_username,influencer_type,influencer_location)
    # posts_count = 1
    influencer_post_data = post_scraper(instagram_username,posts_count)
    combined_influencer_data = influencer_basic_data | influencer_post_data
    # add_influencer_to_db(combined_influencer_data)

    def unique_key_check_airtable(column_name,unique_value,table_name):
        try:
            api = Api(AIRTABLE_API_KEY)
            airtable_obj = api.table(AIRTABLE_BASE_ID, table_name)
            records = airtable_obj.all()
            # print(f"\nCompleted unique key check")
            return any(record['fields'].get(column_name) == unique_value for record in records) 
        except Exception as e:
            print(f"Error occured in {__name__} while performing unique value check in airtable. {e}")

    # function to export data to Airtable
    def export_to_airtable(data,raw_table):
        try:
            # print(f"\nExporting results to Airtable")
            api = Api(AIRTABLE_API_KEY)
            airtable_obj = api.table(AIRTABLE_BASE_ID, raw_table)
            response = airtable_obj.create(data)
            if 'id' in response:
                print("Record inserted successfully:", response['id'])
            else:
                print("Error inserting record:", response)
        except Exception as e:
            print(f"Error occured in {__name__} while exporting the data to Airtable. {e}")

    record_exists = unique_key_check_airtable('instagram_url',combined_influencer_data["instagram_url"],"src_influencer_data")
    if not record_exists:
        print(f"Record doesn't exist")
        export_to_airtable(combined_influencer_data,"src_influencer_data")
    else:
        print(f"Record Exists")

# At the top of data_collection.py
import asyncio
from apify_client import ApifyClientAsync
from config import APIFY_API_TOKEN

client_async = ApifyClientAsync(APIFY_API_TOKEN)

# async def get_engagement_rate(usernames: list):
#     try:
#         input_object = {"usernames": usernames}
#         # run = await client_async.actor("mraxes~instagram-profile-analisation").call(run_input=input_object)
#         run = await client_async.actor("powerful_bachelor/instagram-profile-scraper-pro").call(run_input=input_object)
        
#         dataset_id = run.get("defaultDatasetId")
#         dataset_client = client_async.dataset(dataset_id)

#         dataset_items_response = await dataset_client.list_items()  # await coroutine
#         items = dataset_items_response.items  # access ListPage.items

#         engagement_data = [
#             {"username": item.get("username"), 
#              "engagement_rate": item.get("engagement_rate"),
#              "average_likes": item.get("average_likes"),
#             "average_comments": item.get("average_comments"),
#             "average_views": item.get("average_views")}
#             for item in items
#         ]
#         return engagement_data
#     except Exception as e:
#         print(f"Error fetching engagement rate: {e}")
#         return []
# import asyncio
# from flask import jsonify
# from airtable import Table

# ------------------ ENGAGEMENT RATE FETCH ------------------
# async def get_engagement_rate(usernames: list):
#     try:
#         input_object = {"usernames": usernames}
#         run = await client_async.actor(
#             "powerful_bachelor/instagram-profile-scraper-pro"
#         ).call(run_input=input_object)
        
#         dataset_id = run.get("defaultDatasetId")
#         dataset_client = client_async.dataset(dataset_id)

#         dataset_items_response = await dataset_client.list_items()
#         items = dataset_items_response.items

#         engagement_data = [
#             {
#                 "username": item.get("username"),
#                 "engagement_rate": item.get("engagement_rate"),
#                 "average_likes": item.get("average_likes"),
#                 "average_comments": item.get("average_comments"),
#                 "average_views": item.get("average_views"),
#                 "instagram_url" : safe_str(item.get("url") or item.get("inputUrl")),
#                 "instagram_username" : safe_str(item.get("username")),
#                 "full_name" : safe_str(item.get("fullName")),
#                 "instagram_bio" : safe_str(item.get("biography"))
#                 "external_urls" : safe_str(item.get("externalUrls") or item.get("externalUrl")),
#                 "instagram_followers_count" : safe_int(item.get("followersCount")),
#                 "instagram_follows_count" : safe_int(item.get("followsCount")),
#                 "business_category_name" : safe_str(item.get("businessCategoryName")),
#                 "instagram_profile_pic" : safe_str(item.get("profilePicUrl")),
#                 "instagram_posts_count" : safe_int(item.get("postsCount")),
#             }
#             for item in items
#         ]
#         return engagement_data
#     except Exception as e:
#         print(f"❌ Error fetching engagement rate: {e}")
#         return []


