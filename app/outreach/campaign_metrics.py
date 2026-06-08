import requests
import json
from datetime import datetime, timezone
import pytz
from db.db_utils import update_record,export_to_airtable,retrieve_column_value
from error_logger import execute_error_block

def update_linkedin_campaign_metrics(campaign_id):
  try:
    # Define the timezone
    ny_tz = pytz.timezone("America/New_York")

    campaign_name = retrieve_column_value(table_name="linkedin_campaigns",primary_key_col="campaign_id",primary_key_value=campaign_id,column_name="campaign_name")
    today = datetime.now()
    year, month, day = today.year, today.month, today.day
    print(year, month, day)

    # Get the timestamp for March 12, 2025, 00:00:00 ET
    start_date = ny_tz.localize(datetime(year, month, day, 0, 0, 0))
    start_timestamp = int(start_date.timestamp())

    # Get the timestamp for today (current time) in ET
    end_date = datetime.now(pytz.utc).astimezone(ny_tz)  # Current time in New York
    end_timestamp = int(end_date.timestamp())


    print("From (start):", start_timestamp)
    print("To (end):", end_timestamp)

    url = f"https://api.multilead.io/api/open-api/v1/users/27955/accounts/26967/statistics?from={start_timestamp}&to={end_timestamp}&curves=[3,4,5,6,7,8,9]&campaignId={campaign_id}&timeZone=Europe/Belgrade"

    payload={}
    headers = {
    'Authorization': '23927b94-3ff1-48f2-a726-1730414bc27e',
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    campaign_metrics = json.loads(response.text).get("result").get("dailyStatistic")
    print(campaign_metrics)

    # # 3 INVITATION_SENT,4 MESSAGE_SENT ,5 INMAIL_SENT ,6 INVITATION_ACCEPTED,7 MESSAGE_REPLY,8 INVITATION_ACCEPTED_RATE,9 MESSAGE_REPLY_RATE

    campaign_info = {}
    campaign_info['campaign_id'] = campaign_name
    for metric in campaign_metrics.keys():
      if metric == '3':
        campaign_info["invitations_sent"] = (campaign_metrics[metric])
      elif metric == '4':
        campaign_info["messages_sent"] = (campaign_metrics[metric])
      elif metric == '5':
        campaign_info["inmails_sent"] = (campaign_metrics[metric])
      elif metric == '6':
        campaign_info["invitations_accepted"] = (campaign_metrics[metric])
      elif metric == '7':
        campaign_info["message_replies"] = (campaign_metrics[metric])
      elif metric == '8':
        campaign_info["invitation_accepted_rate"] = (campaign_metrics[metric])
      elif metric == '9':
        campaign_info["message_reply_rate"] = (campaign_metrics[metric])

    metric_dates = len(campaign_info['invitations_sent'])
    for index in range(metric_dates):
      record = {}
      date = campaign_info["invitations_sent"][index]['date']
      record["metrics_date"] = str(date)
      record["linkedin_campaign_name"] = str(campaign_name)
      record["invitations_sent"]= str(campaign_info["invitations_sent"][index]['value'])
      record["messages_sent"]= str(campaign_info["messages_sent"][index]['value'])
      record["inmails_sent"]= str(campaign_info["inmails_sent"][index]['value'])
      record["invitations_accepted"]= str(campaign_info["invitations_accepted"][index]['value'])
      record["message_replies"]= str(campaign_info["message_replies"][index]['value'])
      record["invitation_accepted_rate"]= str(campaign_info["invitation_accepted_rate"][index]['value'])
      record["message_reply_rate"]= str(campaign_info["message_reply_rate"][index]['value'])
      update_status = update_record("linkedin_campaign_metrics",record,"metrics_date")
      if not update_status:
        export_to_airtable(record,"linkedin_campaign_metrics")
      return "Successfully updated the linkedin campaign metrics"
  except Exception as e:
    error = f"Error occured while updating the linkedin campaign metrics. Error: {e}"
    return f"Failed to update the linkedin campaign metrics: {error}"