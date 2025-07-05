import requests, os
import logging
from flask import Blueprint, request, jsonify, current_app
from extensions import db
from services import token_required
from sqlalchemy import text
from models import QuestComment

comments_bp = Blueprint('comments', __name__)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL")
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")


@comments_bp.route('/comments', methods=['GET'])
@token_required
def get_comments():
    """Get all comments from the database.

    Returns:
        JSON: List of all comments
    """
    try:
        comments = db.session.execute(text("SELECT * FROM quest_comments")).fetchall()
        comments_list = [dict(row) for row in comments]
        return jsonify(comments_list), 200
    except Exception as e:
        logging.error("Error in get_comments: %s", e, exc_info=True)
        return jsonify({"error": "An internal error has occurred"}), 500

@comments_bp.route('/comments/<quest_id>', methods=['GET'])
@token_required
def get_comments_by_quest(quest_id):
    try:
        # Step 1: Get comments from DB
        comments = (
            db.session.query(QuestComment)
            .filter_by(quest_id=quest_id)
            .order_by(QuestComment.date_added.desc())
            .all()
        )
    
        # Step 2: Extract unique user_ids
        user_ids = list({comment.user_id for comment in comments})
        
        # Step 3: Call auth service to get usernames
        auth_response = requests.post(
            f"{AUTH_SERVICE_URL}/internal/users/usernames",
            json={"user_ids": user_ids},
            headers={"INTERNAL-SECRET": INTERNAL_SECRET}
        )

        if auth_response.status_code != 200:
            current_app.logger.error(
                "Failed to fetch usernames from auth service: %s", auth_response.text
            )
            return jsonify({
                "error": "Internal server error",
                "message": "An internal error has occurred."
            }), 500

        user_data = auth_response.json()  # { user_id: username }

        # Step 4: Attach usernames to comments
        response = []
        for comment in comments:
            response.append({
                "comment": comment.comment,
                "date_added": comment.date_added,
                "user_id": comment.user_id,
                "username": user_data.get(comment.user_id, "Unknown")
            })

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error("Error in get_comments_by_quest: %s", e, exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": "An internal error has occurred."
        }), 500

@comments_bp.route('/comments/<quest_id>', methods=['POST'])
@token_required
def add_comment(quest_id):
    """Add a comment to a specific quest."""
    try:
        data = request.get_json()
        comment = data.get('comment')
        user_id = data.get('user_id')
        
        if not comment or not comment.strip():
            return jsonify({"error": "Comment is required"}), 400

        new_comment = QuestComment(
            quest_id=quest_id,
            user_id=user_id,
            comment=comment.strip()
        )
        db.session.add(new_comment)
        db.session.commit()

        return jsonify({"message": "Comment added successfully"}), 201
    except Exception as e:
        current_app.logger.error("Error in add_comment: %s", e, exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": "An internal error has occurred."
        }), 500
