from flask import Flask, request, jsonify
from db.db_ops import db_manager
app = Flask(__name__)

def calculate_metrics(username, reach_rate):
    try:
        table_name = "src_influencer_data_demo"
        cols_list = ["tiktok_username"]
        col_values = [username]
        result = db_manager.get_records_with_filter(table_name, cols_list, col_values, limit=1)

        if not result:
            return {"status": "failed", "message": f"No record found for {username}"}, 404

        record = result if isinstance(result, dict) else result[0]
        print(f"✅ Record: {record}", flush=True)

        followers = record.get("tiktok_followers_count", 0)
        import ast

        comments = record.get("tiktok_comment_count", [])
        likes = record.get("tiktok_digg_count", [])

        # Convert from string to list if needed
        if isinstance(likes, str):
            try:
                likes = ast.literal_eval(likes)
            except Exception as e:
                return {"status": "failed", "error": f"Invalid likes format: {e}"}, 400

        if isinstance(comments, str):
            try:
                comments = ast.literal_eval(comments)
            except Exception as e:
                return {"status": "failed", "error": f"Invalid comments format: {e}"}, 400

        followers_count = int(followers)

        if not isinstance(likes, list) or not isinstance(comments, list):
            return {"status": "failed", "error": "Likes and comments must be lists"}, 400

        likes_count = [int(l) for l in likes if isinstance(l, (int, float, str)) and str(l).strip().isdigit()]
        comments_count = [int(c) for c in comments if isinstance(c, (int, float, str)) and str(c).strip().isdigit()]

        avg_likes = sum(likes_count) / len(likes_count) if likes_count else 0
        avg_comments = sum(comments_count) / len(comments_count) if comments_count else 0

        if followers_count <= 0:
            return {"status": "failed", "error": "Invalid follower count"}, 400

        engagement_rate = ((avg_likes + avg_comments) / followers_count) * 100
        estimated_reach = followers_count * reach_rate
        update_data = {
            "id":  record["id"],
            "engagement_rate": round(engagement_rate, 2),
            "estimated_reach": int(estimated_reach)
        }
        db_manager.update_multiple_fields(table_name, update_data, "id")

        return {
            "status": "success",
            "total_likes": likes_count,
            "total_comments": comments_count,
            "engagement_rate": round(engagement_rate, 2),
            "estimated_reach": int(estimated_reach)
        }, 200

    except Exception as e:
        return {"status": "failed", "error": str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)
