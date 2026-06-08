import requests    
from flask import Flask, request, jsonify

app = Flask(__name__)

# Airtable API details
AIRTABLE_API_KEY = "patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3"
BASE_ID = "app5s8zl7DsUaDmtx"
TABLE_NAME = "client_config"

AIRTABLE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def find_record_by_client_id(client_id):
    """Fetch the record ID for a given client_id."""
    params = {"filterByFormula": f"client_id='{client_id}'"}
    response = requests.get(AIRTABLE_URL, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        records = response.json().get("records", [])
        if records:
            return records[0]["id"]  # Return first matched record ID
    return None

@app.route("/update_client_configuration_form", methods=["GET"])
def update_client_configuration():
    try:
        # Read form data instead of JSON
        client_id = request.form.get("client-id")  # Match the field name in CF7

        # Get repeated fields as lists
        icp_job_seniorities = request.form.getlist("icp-job-seniorities[]")
        icp_job_details = request.form.getlist("icp-job-details[]")
        icp_locations = request.form.getlist("icp-locations[]")
        organization_domains = request.form.getlist("organization-domains[]")

        if not client_id:
            return jsonify({"success": False, "message": "Missing required field: client_id"}), 400

        # Convert lists to JSON strings before storing in Airtable
        airtable_data = {
            "records": [
                {
                    "fields": {
                        "client_id": client_id,
                        "icp_job_seniorities": json.dumps(icp_job_seniorities, ensure_ascii=False),
                        "icp_job_details": json.dumps(icp_job_details, ensure_ascii=False),
                        "icp_locations": json.dumps(icp_locations, ensure_ascii=False),
                        "organization_domains": json.dumps(organization_domains, ensure_ascii=False)
                    }
                }
            ]
        }

        # Send data to Airtable
        response = requests.post(AIRTABLE_URL, json=airtable_data, headers=HEADERS)

        if response.status_code in [200, 201]:
            return jsonify({"success": True, "message": "Data saved successfully", "response": response.json()}), 201
        else:
            return jsonify({"success": False, "message": "Failed to save data", "error": response.text}), response.status_code

    except Exception as e:
        return jsonify({"success": False, "message": "Internal Server Error", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
