import os, requests
from flask import Blueprint, request, jsonify, send_file
from extensions import db
from services import token_required
from sqlalchemy import text
from models import Quest, ReportedQuest
from dotenv import load_dotenv

load_dotenv()

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL")
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")

quests_bp = Blueprint('quests', __name__)

# Get all quests
@quests_bp.route('/quests', methods=['GET'])
@token_required
def get_quests():
    """Get all quests from the database.

    Returns:
        JSON: List of all quests
    """
    try:
        result = db.session.execute(text("SELECT * FROM coding_quests"))
        quests = [dict(row._mapping) for row in result.fetchall()]
        return jsonify(quests), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all quests filtered by language
@quests_bp.route('/quests/<language>', methods=['GET'])
@token_required
def get_quests_by_language(language):
    """Get all quests filtered by language.

    Args:
        language (str): Programming language

    Returns:
        JSON: List of quests filtered by language
    """

    try:
        result = db.session.execute(text("SELECT * FROM coding_quests WHERE language = :language"), {"language": language})
        quests = [dict(row._mapping) for row in result.fetchall()]
        return jsonify(quests)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Open a specific quest by its ID
@quests_bp.route('/quest/<quest_id>', methods=['GET'])
@token_required
def open_quest(quest_id):
    """Get a specific quest by its ID.

    Args:
        quest_id (str): Quest ID

    Returns:
        JSON: Quest details
    """

    try:
        result = db.session.execute(text("SELECT * FROM coding_quests WHERE id = :quest_id"), {'quest_id': quest_id})
        quest = result.fetchone()
        if not quest:
            return jsonify({"error": "Quest not found"}), 404
        return jsonify({
            "quest_id": quest.id,
            "language": quest.language,
            "difficulty": quest.difficulty,
            "quest_name": quest.quest_name,
            "solved_times": quest.solved_times,
            "quest_author": quest.quest_author,
            "date_added": quest.date_added.isoformat(),
            "last_modified": quest.last_modified.isoformat(),
            "condition": quest.condition,
            "function_template": quest.function_template,
            "xp": quest.xp,
            "type": quest.type
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Create a new quest (as Admin)    
@quests_bp.route('/quests', methods=['POST'])
@token_required
def add_new_quest():
    """Add a new quest to the database.

    Returns:
        JSON: Newly created quest
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    try:
        auth_response = requests.post(
            f"{AUTH_SERVICE_URL}/internal/users/usernames",
            json={"user_ids": [data['quest_author']]},
            headers={"INTERNAL-SECRET": INTERNAL_SECRET}
        )
        quest_author_data = auth_response.json()
        quest_author_id = next(iter(quest_author_data.keys()))
        quest_author_username = quest_author_data[quest_author_id]
        new_quest = Quest(
            language=data['language'],
            difficulty=data['difficulty'],
            quest_name=data['quest_name'],
            quest_author=quest_author_username,
            condition=data['condition'],
            function_template=data['function_template'],
            unit_tests=data['unit_tests'],
            test_inputs=data.get('test_inputs'),
            test_outputs=data.get('test_outputs'),
            xp="30" if data['difficulty'] == "Easy" else "60" if data['difficulty'] == "Medium" else "100",
            type=data.get('type')
        )
        db.session.add(new_quest)
        db.session.commit()
        return jsonify({"message": "Quest added successfully", "quest_id": new_quest.quest_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Open a quest (as Admin)
@quests_bp.route('/edit_quest/<quest_id>', methods=['GET'])
@token_required
def open_edit_quest(quest_id):
    """Get a specific quest by its ID for editing.

    Args:
        quest_id (str): Quest ID

    Returns:
        JSON: Quest details for editing
    """

    try:
        result = db.session.execute(text("SELECT * FROM coding_quests WHERE id = :quest_id"), {'quest_id': quest_id})
        quest = result.fetchone()
        if not quest:
            return jsonify({"error": "Quest not found"}), 404
        
        # Collect dynamic inputs and outputs (from input_0 to input_9 and output_0 to output_9)
        inputs = [getattr(quest, f'input_{i}') for i in range(10) if getattr(quest, f'input_{i}') is not None]
        outputs = [getattr(quest, f'output_{i}') for i in range(10) if getattr(quest, f'output_{i}') is not None]
        
        return jsonify({
            "quest_id": quest.id,
            "language": quest.language,
            "difficulty": quest.difficulty,
            "quest_name": quest.quest_name,
            "solved_times": quest.solved_times,
            "quest_author": quest.quest_author,
            "date_added": quest.date_added.isoformat() if quest.date_added else None,
            "last_modified": quest.last_modified.isoformat() if quest.last_modified else None,
            "condition": quest.condition,
            "function_template": quest.function_template,
            "inputs": inputs,
            "outputs": outputs,
            "example_solution": quest.example_solution,
            "xp": quest.xp,
            "type": quest.type
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Edit a quest (as Admin) by its ID
@quests_bp.route('/quests/<quest_id>', methods=['PUT'])
@token_required
def edit_quest(quest_id):
    """Edit a quest as Admin by its ID.
    
    Args:
        quest_id (str): Quest ID
    
    Returns:
        JSON: Updated quest details
    """
    data = request.get_json()
    
    if not quest_id:
        return jsonify({"error": "No quest ID provided"}), 400
    
    try:
        quest = db.session.query(Quest).filter_by(id=quest_id).first()
        if not quest:
            return jsonify({"error": "Quest not found"}), 404

        # Update basic attributes
        quest.language = data.get('language', quest.language)
        quest.difficulty = data.get('difficulty', quest.difficulty)
        quest.quest_name = data.get('quest_name', quest.quest_name)
        quest.condition = data.get('condition', quest.condition)
        quest.example_solution = data.get('example_solution', quest.example_solution)
        quest.xp = "30" if quest.difficulty == "Easy" else "60" if quest.difficulty == "Medium" else "100"
        quest.type = data.get('type', quest.type)
        quest.last_modified = db.func.now()

        # Update inputs and outputs (input_0 to input_9, output_0 to output_9)
        for i in range(10):
            input_key = f"input_{i}"
            output_key = f"output_{i}"
            if input_key in data:
                setattr(quest, input_key, data[input_key])
            if output_key in data:
                setattr(quest, output_key, data[output_key])

        db.session.commit()
        return jsonify({"message": "Quest updated successfully"}), 200
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error editing quest {quest_id}: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

# Create reported quest
@quests_bp.route('/report_quest/<quest_id>', methods=['POST'])
@token_required
def report_quest(quest_id):
    """Report a quest by its ID.

    Args:
        quest_id (str): Quest ID

    Returns:
        JSON: Confirmation message
    """
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'reason' not in data:
        return jsonify({"error": "Invalid data provided"}), 400
    try:
        reported_quest = ReportedQuest(
            quest_id=quest_id,
            user_id=data['user_id'],
            reason=data['reason']
        )
        db.session.add(reported_quest)
        db.session.commit()
        return jsonify({"message": "Quest reported successfully"}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.exception(f"Error reporting quest {quest_id}")
        return jsonify({"error": "An internal error occurred"}), 500
    
