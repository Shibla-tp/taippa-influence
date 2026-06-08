import requests

url = "https://api.instantly.ai/api/v2/leads"

headers = {
  "Content-Type": "application/json",
  "Authorization": "Bearer YzIxN2JhMWYtZjFiOC00Njc1LThiYTUtNjJiY2YyYmUwNWUxOmZqeW5YVUp2Rkdpcw=="
}

payload = {
  "campaign": "2441391c-e88d-498d-86ce-f5e10e7018bf",
  "email": "isravanram@gmail.com",
  "personalization": "Hello, how are you?",
  "custom_variables": {
    "Subject": "Intro",
    "FollowUpEmail": "Just a follow-up email test message"
  }
}

response = requests.post(url, json=payload, headers=headers)

data = response.json()
print(data)