import requests, os
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt_identity
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv
import logging
import app

logging.basicConfig(level=logging.ERROR)


def token_required(f):
    """Decorator to check if the request has a valid JWT token.

    Args:
        f (object): function to be decorated

    Returns:
        function object: function
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception as e:
            app.logging.error(f"JWT verification failed: {e}")
            return jsonify({"error": "Unauthorized", "message": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

def get_username_from_auth(user_id):
    try:
        response = requests.get(
            f"{os.getenv("AUTH_SERVICE_URL")}/users/{user_id}",
            headers={"Authorization": f"Bearer {os.getenv('INTERNAL_SECRET')}"}
        )
        if response.status_code == 200:
            return response.json().get("username", "Unknown")
    except Exception as e:
        return f"Error fetching username for user_id {user_id}: {e}"
    return "Unknown"