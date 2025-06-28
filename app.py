import logging
import os
from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db, jwt, migrate
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Set up logging
    if not app.logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        
    app.logger.setLevel(logging.INFO)

    CORS(app, resources={r"/*": {"origins": "*"}})
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    from quests_routes import quests_bp
    from comments_routes import comments_bp
    from quest_submisions_routes import quests_submissions_bp
    app.register_blueprint(quests_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(quests_submissions_bp)

    with app.app_context():
        db.create_all()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5003, debug=True)