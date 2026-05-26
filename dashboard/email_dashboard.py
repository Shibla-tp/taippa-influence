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

def fetch_recent_leads_from_db(client_id):
    try:
        conn = connect_to_postgres()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Step 1: Get campaign ID for client
        cur.execute("""
            SELECT instantly_campaign_id 
            FROM client_info 
            WHERE client_id = %s
        """, (client_id,))
        client_row = cur.fetchone()

        if not client_row:
            return {"error": "Client not found"}, 404

        campaign_id = client_row['instantly_campaign_id']

        # Step 2: Fetch recent replies
        cur.execute("""
            SELECT full_name, email, linkedin_profile_url, sentiment, photo_url
            FROM email_response_guideline
            WHERE campaign_id = %s
            ORDER BY created_time DESC
            LIMIT 5
        """, (campaign_id,))
        leads = cur.fetchall()

        return {"client_id": client_id, "recent_leads": leads}, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if conn:
            conn.close()

def fetch_metric_value(username, field):
    try:
        conn = connect_to_postgres()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Step 1: Get campaign ID from client_info
        cursor.execute("""
            SELECT instantly_campaign_id 
            FROM client_info 
            WHERE client_id = %s
            LIMIT 1;
        """, (username,))
        result = cursor.fetchone()

        if not result or 'instantly_campaign_id' not in result:
            return 0

        instantly_campaign_id = result['instantly_campaign_id']

        # Step 2: Fetch the desired metric
        cursor.execute(f"""
            SELECT {field} 
            FROM metrics 
            WHERE campaign_id = %s
            LIMIT 1;
        """, (instantly_campaign_id,))
        metric_result = cursor.fetchone()

        return int(metric_result[field]) if metric_result and field in metric_result else 0

    except Exception as e:
        print("Error:", e)
        return 0

    finally:
        if conn:
            cursor.close()
            conn.close()

def get_booking_count():
    try:
        client_id = request.args.get("client_id")
        if not client_id:
            return jsonify({"error": "client_id is required"}), 400

        conn = connect_to_postgres()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT COUNT(*) FROM booking_records WHERE client_id = %s", (client_id,))
        result = cursor.fetchone()

        booking_count = result['count'] if result and 'count' in result else 0

        return jsonify({"value": booking_count}), 200

    except Exception as e:
        print("Error in get_booking_count_dashboard:", e)
        return jsonify({"error": "Internal Server Error"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def email_sent_chart(username):
    try:
        conn = connect_to_postgres()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Step 1: Get the campaign ID from client_info
        cursor.execute("""
            SELECT instantly_campaign_id 
            FROM client_info 
            WHERE client_id = %s
        """, (username,))
        result = cursor.fetchone()
        if not result or not result['instantly_campaign_id']:
            return jsonify({'error': 'No campaign ID found'}), 404

        campaign_id = result['instantly_campaign_id']

        # Step 2: Determine current week's start and end dates
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        end_of_week = start_of_week + timedelta(days=6)          # Sunday

        # Step 3: Fetch email records from dashboard_inbox within the week
        cursor.execute("""
            SELECT created 
            FROM dashboard_inbox 
            WHERE campaign_id = %s
            AND CAST(created AS date) >= %s 
            AND CAST(created AS date) <= %s
        """, (campaign_id, start_of_week.date(), end_of_week.date()))
        emails = cursor.fetchall()

        # Step 4: Aggregate email count by day of week
        day_counts = {'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0, 'Sat': 0, 'Sun': 0}
        for row in emails:
            try:
                created_date = datetime.strptime(row['created'], '%Y-%m-%d')
            except:
                created_date = row['created']  # If already a datetime
            created_day = created_date.strftime('%a')
            if created_day in day_counts:
                day_counts[created_day] += 1

        return jsonify(day_counts)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if conn:
            conn.close()

def get_campaign_details(username):
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
            campaign_id = campaign.get('instantly_campaign_id')
            profile_pictures = []

            try:
                cursor.execute("""
                    SELECT photo_url
                    FROM email_response_guideline
                    WHERE campaign_id = %s
                    ORDER BY created_time DESC
                    LIMIT 5
                """, (campaign_id,))
                replies = cursor.fetchall()
                profile_pictures = [reply['photo_url'] for reply in replies]

            except errors.UndefinedTable:
                
                profile_pictures = []

            campaign['profile_pictures'] = profile_pictures
            campaign_data.append(campaign)

        cursor.close()
        conn.close()

        return jsonify({'campaigns': campaign_data})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

def fetch_leads(user_id):
    try:
        conn = connect_to_postgres()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Step 1: Fetch campaign IDs and cleaned table
        cur.execute("""
            SELECT instantly_campaign_id, cleaned_table
            FROM client_info
            WHERE client_id = %s
        """, (user_id,))
        rows = cur.fetchall()

        campaign_ids = [row['instantly_campaign_id'] for row in rows if row['instantly_campaign_id']]
        cleaned_table = next((row['cleaned_table'] for row in rows if row['cleaned_table']), None)

        if not campaign_ids or not cleaned_table:
            return {'error': 'Campaigns or cleaned_table not found'}

        # Step 2: Fetch replies
        placeholders = ','.join(['%s'] * len(campaign_ids))
        cur.execute(f"""
            SELECT *
            FROM email_response_guideline
            WHERE campaign_id IN ({placeholders})
            ORDER BY created_time DESC
            LIMIT 50
        """, campaign_ids)
        replies = cur.fetchall()

        # Step 3: Fetch profile data
        emails = list(set([reply['email'] for reply in replies if reply.get('email')]))
        profiles = {}
        if emails:
            email_placeholders = ','.join(['%s'] * len(emails))
            sanitized_table = cleaned_table.strip().replace('"', '').replace(';', '')

            cur.execute(f"""
                SELECT *
                FROM {sanitized_table}
                WHERE email IN ({email_placeholders})
            """, emails)
            profile_rows = cur.fetchall()
            profiles = {row['email']: row for row in profile_rows}

        # Combine replies and profiles
        combined = []
        for reply in replies:
            email = reply.get('email')
            combined.append({
                'reply': reply,
                'profile': profiles.get(email, {})
            })

        return combined

    except Exception as e:
        return {'error': str(e)}

    finally:
        if conn:
            cur.close()
            conn.close()

#client_details_page on email dashboard
def get_user_campaigns(client_id):
    try:
        conn = connect_to_postgres()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Fetch campaigns
        cur.execute("""
            SELECT instantly_campaign_id, campaign_name, status, created_date 
            FROM campaign_details 
            WHERE client_id = %s
        """, (client_id,))
        campaigns = cur.fetchall()

        campaign_list = []
        for campaign in campaigns:
            campaign_id = campaign['instantly_campaign_id']
            name = campaign['campaign_name']
            status = campaign['status']
            created = campaign['created_date']

            # Fetch 5 recent email_response_guideline entries (photo_url)
            cur.execute("""
                SELECT photo_url FROM email_response_guideline
                WHERE campaign_id = %s
                ORDER BY created_time DESC
                LIMIT 5
            """, (campaign_id,))
            photos = cur.fetchall()
            photo_urls = [p['photo_url'] if p['photo_url'] else 'https://taippa.com/wp-content/uploads/2025/05/avatar-e1747306750362.png' for p in photos]

            if isinstance(created, str):
                created_date = created  # already formatted
            else:
                created_date = created.strftime("%Y-%m-%d")

            campaign_list.append({
                "campaign_id": campaign_id,
                "campaign_name": name,
                "status": status,
                "created_date": created_date,
                "profile_pictures": photo_urls
            })

        cur.close()
        conn.close()
        return campaign_list

    except Exception as e:
        raise Exception(f"Error fetching campaigns: {e}")


def get_campaign_metrics(campaign_id):
    try:
        conn = connect_to_postgres()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT opened, clicked, sequence_started, replies_received
            FROM metrics
            WHERE campaign_id = %s
        """, (campaign_id,))
        result = cur.fetchone()

        cur.close()
        conn.close()

        if result:
            return {
                "email_opened": result["opened"],
                "email_clicked": result["clicked"],
                "sequence_started": result["sequence_started"],
                "replies_received": result["replies_received"]
            }
        else:
            raise Exception("No data found")

    except Exception as e:
        raise Exception(f"Error fetching metrics: {str(e)}")


def get_lead_details(username, lead_email):
    conn = connect_to_postgres()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Get the cleaned_table name
        cur.execute("SELECT cleaned_table FROM client_info WHERE client_id = %s", (username,))
        result = cur.fetchone()
        if not result:
            raise Exception('No campaign found for client_id: ' + username)

        cleaned_table = result['cleaned_table']

        # Fetch lead details
        query = f"SELECT * FROM {cleaned_table} WHERE email = %s LIMIT 1"
        cur.execute(query, (lead_email,))
        lead = cur.fetchone()

        if not lead:
            raise Exception('No lead found with email: ' + lead_email)

        return dict(lead)

    except Exception as e:
        raise e

    finally:
        cur.close()
        conn.close()

    
if __name__ == '__main__':
    app.run(debug=True)
