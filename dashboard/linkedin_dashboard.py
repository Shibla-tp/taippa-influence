from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from psycopg2 import errors
from db.db_ops import db_manager
app = Flask(__name__)

def connect_to_postgres():
    return psycopg2.connect(
        dbname="taippa",
        user="super",
        password="drowsapp_2025",
        host="magmostafa-4523.postgres.pythonanywhere-services.com",
        port="14523"
    )




def get_linkedin_metrics(username: str):
    """Return LinkedIn-campaign metrics for the given client_id."""
    conn = connect_to_postgres()
    cur  = conn.cursor()

    # 1️⃣  find the user’s LinkedIn campaign
    cur.execute(
        "SELECT linkedin_campaign_name "
        "FROM campaign_details "
        "WHERE client_id = %s "
        "LIMIT 1",
        (client_id,),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError("No LinkedIn campaign found for this user")

    linkedin_campaign_name = row[0]

    # 2️⃣  pull the metrics
    cur.execute(
        """
        SELECT metrics_date,
               invitations_sent,
               messages_sent,
               inmails_sent,
               invitations_accepted,
               message_replies,
               invitation_accepted_rate,
               message_reply_rate
        FROM linkedin_campaign_metrics
        WHERE linkedin_campaign_name = %s
        ORDER BY metrics_date DESC
        """,
        (linkedin_campaign_name,),
    )
    cols = [c[0] for c in cur.description]
    results = [dict(zip(cols, r)) for r in cur.fetchall()]

    cur.close()
    conn.close()
    return results


def get_linkedin_campaign_details(username):
    if not username:
        return jsonify({'error': 'Missing username'}), 400

    try:
        conn = connect_to_postgres()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        
        cursor.execute("""
            SELECT * FROM campaign_details
            WHERE client_id = %s
        """, (username,))
        campaigns = cursor.fetchall()

        if not campaigns:
            return jsonify({'message': 'No campaigns found'}), 404

        campaign_data = []

        for campaign in campaigns:
            campaign_name = campaign.get('linkedin_campaign_name')
            profile_pictures = []

            try:
                cursor.execute("""
                    SELECT picture
                    FROM leadsin_response_linkedin
                    WHERE campaign_name = %s
                    ORDER BY created_time DESC
                    LIMIT 5
                """, (campaign_name,))
                replies = cursor.fetchall()
                profile_pictures = [reply['picture'] for reply in replies]

            except errors.UndefinedTable:
                
                profile_pictures = []

            campaign['profile_pictures'] = profile_pictures
            campaign_data.append(campaign)

        cursor.close()
        conn.close()

        return jsonify({'campaigns': campaign_data})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
def get_linkedin_statistics(username, field):
    conn = connect_to_postgres()
    cur = conn.cursor()

    # Get campaign name
    cur.execute("SELECT linkedin_campaign_name FROM campaign_details WHERE client_id = %s LIMIT 1", (username,))
    row = cur.fetchone()

    if not row:
        return None  # Let the route handler handle this case

    linkedin_campaign_name = row[0]

    if field:
        cur.execute(f"SELECT SUM(CAST({field} AS INTEGER)) FROM linkedin_campaign_metrics WHERE linkedin_campaign_name = %s", (linkedin_campaign_name,))
        total = cur.fetchone()[0] or 0
        return {field: total}
    else:
        cur.execute("SELECT COUNT(*) FROM linkedin_campaign_metrics WHERE linkedin_campaign_name = %s", (linkedin_campaign_name,))
        total = cur.fetchone()[0]
        return {"total_records": total}

def get_linkedin_replies(username):
    try:
        print("[DEBUG] Connecting to DB")
        conn = connect_to_postgres()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        print(f"[DEBUG] Fetching campaigns for username: {username}")
        cursor.execute("""
            SELECT linkedin_campaign_name 
            FROM campaign_details 
            WHERE client_id = %s
        """, (username,))
        rows = cursor.fetchall()
        print("[DEBUG] Campaign rows:", rows)

        campaigns = [row['linkedin_campaign_name'] for row in rows if row['linkedin_campaign_name']]
        print("[DEBUG] Campaigns:", campaigns)

        if not campaigns:
            return []

        print("[DEBUG] Fetching leads")
        cursor.execute("""
            SELECT full_name, email, phone, linkedin_profile_url, message, sentiment, created_time, picture 
            FROM leadsin_response_linkedin
            WHERE campaign_name = ANY(%s)
        """, (campaigns,))
        leads = cursor.fetchall()
        print("[DEBUG] Leads fetched:", leads)

        return leads

    except Exception as e:
        print('[ERROR] Exception occurred:', e)
        # traceback.print_exc()
        return None

    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def get_linkedin_leads_by_username(username):
    if not username:
        return {"error": "Username is required"}, 400

    try:
        conn = connect_to_postgres()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Step 1: Get campaign names
        cursor.execute("SELECT linkedin_campaign_name FROM campaign_details WHERE client_id = %s", (username,))
        campaigns = cursor.fetchall()
        campaign_names = [c['linkedin_campaign_name'] for c in campaigns]

        if not campaign_names:
            return {"leads": []}, 200

        # Step 2: Get all leads for those campaigns
        cursor.execute(
            "SELECT * FROM linkedin_leads WHERE campaign_name = ANY(%s)",
            (campaign_names,)
        )
        leads = cursor.fetchall()

        return {"leads": leads}, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if conn:
            conn.close()

    
if __name__ == '__main__':
    app.run(debug=True)
