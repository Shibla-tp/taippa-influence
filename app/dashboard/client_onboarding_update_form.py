import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Airtable Configuration
AIRTABLE_BASE_ID = "app5s8zl7DsUaDmtx"
AIRTABLE_TABLE_NAME = "client_info"
AIRTABLE_API_KEY = "patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3"
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def get_record_id(client_id):
    """Fetches record_id from Airtable based on client_id."""
    response = requests.get(AIRTABLE_URL, headers=HEADERS)
    if response.status_code == 200:
        records = response.json().get("records", [])
        for record in records:
            if record["fields"].get("client_id") == client_id:
                return record["id"]
    return None


def update_client_onboarding():
    try:
        # Retrieve data from query parameters
        client_id = request.args.get("client_id")
        full_name = request.args.get("full_name")
        email = request.args.get("email")
        job_title = request.args.get("job_title")
        location = request.args.get("location")
        phone = request.args.get("phone")
        company_name = request.args.get("company_name")
        company_website = request.args.get("company_website")
        instantly_campaign_id = request.args.get("instantly_campaign_id")

        if not client_id or not full_name:
            return jsonify({"error": "Missing required fields"}), 400

        record_id = get_record_id(client_id)
        if not record_id:
            return jsonify({"error": "Client not found in Airtable"}), 404

        update_data = {
            "fields": {
                "full_name": full_name,
                "email": email,
                "job_title": job_title,
                "location": location,
                "phone": phone,
                "company_name": company_name,
                "company_website": company_website,
                "instantly_campaign_id": instantly_campaign_id
            }
        }

        response = requests.patch(f"{AIRTABLE_URL}/{record_id}", json=update_data, headers=HEADERS)
        return jsonify(response.json()), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
