import uuid
from extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON


class Quest(db.Model):
    """Quest model for the coding quests database.

    Args:
        db (): SQLAlchemy instance
    """
    __tablename__ = 'coding_quests'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    language = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    quest_name = db.Column(db.String(255), nullable=False)
    solved_times = db.Column(db.Integer, default=0, nullable=True)
    quest_author = db.Column(db.String(255), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.now, nullable=False)
    last_modified = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    condition = db.Column(db.Text, nullable=False)
    function_template = db.Column(db.Text, nullable=False)
    
    # Quest inputs, where input_0 is the null test
    input_0 = db.Column(db.Text, nullable=True)  # Input for the quest
    input_1 = db.Column(db.Text, nullable=True)  # Input for the quest
    input_2 = db.Column(db.Text, nullable=True)  # Input for the quest
    input_3 = db.Column(db.Text, nullable=True)  # Input for the quest
    input_4 = db.Column(db.Text, nullable=True)  # Input for the quest
    input_5 = db.Column(db.Text, nullable=True)  # Input for the quest
    input_6 = db.Column(db.Text, nullable=True)  # Input for the quest
    input_7 = db.Column(db.Text, nullable=True)  # Input for the quest
    input_8 = db.Column(db.Text, nullable=True)  # Input for the quest
    input_9 = db.Column(db.Text, nullable=True)  # Input for the quest
    
    # Quest outputs, where output_0 is the null test
    output_0 = db.Column(db.Text, nullable=True)  # Output for the quest
    output_1 = db.Column(db.Text, nullable=True)  # Output for the quest
    output_2 = db.Column(db.Text, nullable=True)  # Output for the quest
    output_3 = db.Column(db.Text, nullable=True)  # Output for the quest
    output_4 = db.Column(db.Text, nullable=True)  # Output for the quest
    output_5 = db.Column(db.Text, nullable=True)  # Output for the quest
    output_6 = db.Column(db.Text, nullable=True)  # Output for the quest
    output_7 = db.Column(db.Text, nullable=True)  # Output for the quest
    output_8 = db.Column(db.Text, nullable=True)  # Output for the quest
    output_9 = db.Column(db.Text, nullable=True)  # Output for the quest
    
    example_solution = db.Column(db.Text, nullable=True)  # Example solution for the quest
    xp = db.Column(db.Enum('30', '60', '100', name='xp_points'), nullable=False)
    type = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=True)
    quest_comments = db.Column(JSON, default = [], nullable=True) # Store comments for the submited quests
    
    
    
    def __init__(self, language, difficulty, quest_name, quest_author, condition, function_template, unit_tests, test_inputs, test_outputs, xp, type):
        self.language = language
        self.difficulty = difficulty
        self.quest_name = quest_name
        self.quest_author = quest_author
        self.condition = condition
        self.function_template = function_template
        self.unit_tests = unit_tests
        self.test_inputs = test_inputs
        self.test_outputs = test_outputs
        self.xp = xp
        self.type = type


class ReportedQuest(db.Model):
    """ReportedQuest model for the coding quests database.

    Args:
        db (): SQLAlchemy instance
    """
    __tablename__ = 'reported_quests'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quest_id = db.Column(db.String(256), db.ForeignKey('coding_quests.id'), nullable=False)
    user_id = db.Column(db.String(256), nullable=False)  # User UUID
    reason = db.Column(db.Text, nullable=False)
    date_reported = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __init__(self, quest_id, user_id, reason):
        self.quest_id = quest_id
        self.user_id = user_id
        self.reason = reason


class QuestSolution(db.Model):
    """QuestSolution model for the coding quests database.

    Args:
        db (): SQLAlchemy instance
    """
    __tablename__ = 'quest_solutions'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quest_id = db.Column(db.String(256), db.ForeignKey('coding_quests.id'), nullable=False)
    user_id = db.Column(db.String(256), nullable=False)  # User UUID
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    tests_passed = db.Column(db.Integer, default=0, nullable=False)
    tests_failed = db.Column(db.Integer, default=0, nullable=False)
    is_solved = db.Column(db.Boolean, default=False, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.now, nullable=False)


    def __init__(self, quest_id, user_id, code, language, tests_passed=0, tests_failed=0, is_solved=False):
        self.quest_id = quest_id
        self.user_id = user_id
        self.code = code
        self.language = language
        self.tests_passed = tests_passed
        self.tests_failed = tests_failed
        self.is_solved = is_solved


class QuestComment(db.Model):
    """QuestComment model for the coding quests database.

    Args:
        db (): SQLAlchemy instance
    """
    __tablename__ = 'quest_comments'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quest_id = db.Column(db.String(256), db.ForeignKey('coding_quests.id'), nullable=False)
    user_id = db.Column(db.String(256), nullable=False)  # User UUID
    comment = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __init__(self, quest_id, user_id, comment):
        self.quest_id = quest_id
        self.user_id = user_id
        self.comment = comment