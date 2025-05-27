import os
import requests
from flask import jsonify



def update_xp(user_id, quest_xp):
    try:
        response = requests.put(
            f"{os.getenv("USERS_SERVICE_URL")}/users/{user_id}/xp",
            headers={"INTERNAL-SECRET": os.getenv("INTERNAL_SECRET")},
            json={"xp_points": quest_xp}
        )

        if response.status_code == 200:
            print("XP update successful:", response.json())
            return response.json()
        else:
            print("XP update failed:", response.status_code, response.text)
            return jsonify({
                "error": "Failed to update XP",
                "status_code": response.status_code,
                "message": response.text
            }), response.status_code   
    except Exception as e:
        print("Error communicating with users service:", str(e))
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


