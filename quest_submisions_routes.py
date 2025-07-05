import logging
import uuid, os, requests
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from extensions import db
from services import token_required
from sqlalchemy import text
from models import Quest, QuestSolution

from user_progress_func import update_xp

load_dotenv()

quests_submissions_bp = Blueprint('submission', __name__)


# Submit quest solution
@quests_submissions_bp.route('/submit/<quest_id>', methods=['POST'])
@token_required
def quest_solution(quest_id):
    """Submit a solution for a coding quest.
    
    
    Args:
        quest_id (str): The ID of the coding quest.
        
    Returns:
        JSON: Result of the submission including test results and messages.
        
    Raises:
        500: If there is an error during the submission process.
        400: If the request data is invalid or missing required fields.
        
    """
    
    # Get the quest, code, language, and user_id from the request
    code = request.json.get('code')
    language = request.json.get('language')
    quest = db.session.query(Quest).filter_by(id=quest_id).first()
    if not quest:
        return jsonify({"error": "Quest not found"}), 404
    
    quest_xp = quest.xp
    user_id = request.json.get('user_id')
    
    # Max number of tests to run
    MAX_TESTS = 10

    # Hold all the results of the tests and generate UUID for execution
    all_results = {}
    successful_tests = 0
    unsuccessful_tests = 0
    zero_tests = [] # Hold the first example test input and putput
    zero_tests_outputs = [] # Hold the first example after executing the user code (stdout & stderr)
    execution_id = str(uuid.uuid4())
    
    for i in range(MAX_TESTS):
        input_attr = getattr(quest, f'input_{i}', None)
        output_attr = getattr(quest, f"output_{i}", None)
        
        if not input_attr and not output_attr:
            # If both input and output are None, break the loop
            break
        
        if language != 'javascript':
            data = {
                "language": language,
                "version": "*",
                "files": [
                    {
                        "name": f"{user_id}_{quest_id}.{language}",
                        "content": code
                    }
                ],
                "stdin": "\n". join([x for x in input_attr.split(', ') if x.strip()]),
                "args": [],
                "compile_timeout": 5000,
                "run_timeout": 2000,
                "compile_memory_limit": -1,
                "run_memory_limit": -1
            }
        else:
            data = {
                "language": language,
                "version": "*",
                "files": [
                    {
                        "name": f"{user_id}_{quest_id}.{language}",
                        "content": code
                    }
                ],
                "stdin": "",
                "args": [", ".join([x for x in input_attr.split(', ') if x.strip()])],
                "compile_timeout": 5000,
                "run_timeout": 2000,
                "compile_memory_limit": -1,
                "run_memory_limit": -1,
                "execution_id": execution_id
            }
            
        
        # Send the code to the Piston API for execution
        exec_url = os.getenv("PISTON_API_URL") + '/api/v2/execute'
        response = requests.post(exec_url, json=data)
        
        # Check if the response is successful and process the results
        if response.status_code == 200:
            current_output = response.json()['run']['stdout'].strip()
            current_error = response.json()['run']['stderr'].strip()
        
            if str(current_output) == str(output_attr):
                successful_tests += 1
            else:
                unsuccessful_tests += 1
            
            if i == 0:
                zero_tests.append(input_attr)
                zero_tests.append(output_attr)
                zero_tests_outputs.append(current_output)
                zero_tests_outputs.append(current_error)
            
            all_results.update({f"Test {i+1}": {"input": input_attr, 
                                                "output": current_output, 
                                                "expected_output": output_attr, 
                                                "error": current_error}})

        # If the response is not successful, handle the error    
        else:
            message = response.json().get('message', 'Unknown error')
            logs_message = response.json()
            successful_tests = 0
            unsuccessful_tests = i
            zero_tests.append("")
            zero_tests.append("")
            zero_tests_outputs.append("")
            zero_tests_outputs.append("")
            return jsonify({
                "error": f"Execution failed: {message}",
                "logs": logs_message
            }), 500


    # Check if there are any successful or unsuccessful tests
    if not unsuccessful_tests:
        message = 'Congratulations! Your solution is correct!'
        
        # Update the quest solved times
        try:
            quest.solved_times = (quest.solved_times or 0) + 1
            db.session.commit()
        except Exception as e:
            db.session.rollback()
        
        # Update user XP if not already solved
        # Check if the user has already solved this quest
        existing_solution = db.session.query(QuestSolution).filter_by(
            quest_id=quest_id,
            user_id=user_id
        ).first()
        if existing_solution is None or not existing_solution.is_solved:
            # Only update XP if the quest was not solved before
            update_xp(user_id, quest_xp) 
    elif successful_tests and unsuccessful_tests:
        message = 'Your solution is partially correct! Try again!'
    else:
        message = 'Your solution is incorrect! Try again!'

    # Store the solution in the database
    try:
        new_solution = QuestSolution(
            quest_id=quest_id,
            user_id=user_id,
            code=code,
            language=language,
            tests_passed=successful_tests,
            tests_failed=unsuccessful_tests,
            is_solved=(successful_tests == i)
        )
        db.session.add(new_solution)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to store solution in the database"}), 500
    
    # Return the results of the submission
    return jsonify({
        "execution_id": execution_id,
        "quest_id": quest_id,
        "user_id": user_id,
        "successful_tests": successful_tests,
        "unsuccessful_tests": unsuccessful_tests,
        "message": message,
        "zero_tests": zero_tests[0],
        "zero_tests_outputs": zero_tests_outputs[0],
    }), 200
    
# Get all solutions for a specific user
@quests_submissions_bp.route('/solutions/<user_id>', methods=['GET'])
@token_required
def get_user_solutions(user_id):
    """Get all solutions submitted by a specific user.
    
    Args:
        user_id (str): The ID of the user.
        
    Returns:
        JSON: List of solutions submitted by the user.
        
    Raises:
        500: If there is an error during the retrieval process.
    """
    try:
        result = db.session.execute(
            text("SELECT * FROM quest_solutions WHERE user_id = :user_id"),
            {'user_id': user_id}
        )
        solutions = [dict(row._mapping) for row in result.fetchall()]
        
        return jsonify(solutions), 200
    except Exception as e:
        logging.error("Error occurred while retrieving user solutions: %s", e, exc_info=True)
        return jsonify({"error": "An internal error has occurred."}), 500

# Get all correct solutions by user_id
@quests_submissions_bp.route('/correct_solutions/<user_id>', methods=['GET'])
@token_required
def get_quest_solutions(user_id):
    """Get all correct solutions for a specific quest by user_id.
    
    Args:
        quest_id (str): The ID of the quest.
        user_id (str): The ID of the user.
        
    Returns:
        JSON: List of correct solutions for the quest by the user.
        
    Raises:
        500: If there is an error during the retrieval process.
    """
    try:
        result = db.session.execute(
            text("SELECT * FROM quest_solutions WHERE user_id = :user_id AND is_solved = true"),
            {'user_id': user_id}
        )
        solutions = [dict(row._mapping) for row in result.fetchall()]
        
        return jsonify(solutions), 200
    except Exception as e:
        logging.error("Error occurred while retrieving correct solutions: %s", e, exc_info=True)
        return jsonify({"error": "An internal error has occurred."}), 500