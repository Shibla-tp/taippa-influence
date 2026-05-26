from flask import Flask, jsonify, request
import psycopg2

app = Flask(__name__)


def get_profile_picture(username):
    try:
        conn = psycopg2.connect(
            dbname="taippa",
            user="super",
            password="drowsapp_2025",
            host="magmostafa-4523.postgres.pythonanywhere-services.com",
            port="14523"
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT profile_picture FROM client_info WHERE client_id = %s LIMIT 1", 
            (username,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        return jsonify({"profile_picture": row[0] if row else ""})
    except Exception as e:
        return jsonify({"error": str(e)}), 500