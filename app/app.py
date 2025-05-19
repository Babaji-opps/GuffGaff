import os
import logging
from datetime import datetime
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from app import db, Base


# Configure logging
logging.basicConfig(level=logging.DEBUG)

# create the app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or (
    f"sqlite:///../instance/GuffGaff.db"
)
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = "warning"

# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    from app import models  # noqa: F401

    db.create_all()
    
    # Set up user loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))
    # Create a daily challenge for today if none exists
    from app.models import DailyChallenge
    today = datetime.now().date()
    if not DailyChallenge.query.filter_by(date=today).first():
        default_challenges = [
            "Take a photo of something red",
            "Do 10 pushups",
            "Drink 8 glasses of water",
            "Read 10 pages of a book",
            "Meditate for 5 minutes",
            "Go for a 15-minute walk",
            "Try a new food",
            "Write down 3 things you're grateful for",
            "Learn 5 new words in another language",
            "Call a friend you haven't spoken to in a while"
        ]
        import random
        new_challenge = DailyChallenge(
            title=f"Today's Challenge: {random.choice(default_challenges)}",
            description="Complete this challenge and mark it as done to keep your streak going!",
            date=today
        )
        db.session.add(new_challenge)
        db.session.commit()
        logging.debug(f"Created new daily challenge: {new_challenge.title}")

# Import and register the Blueprint after app, db, and login_manager are set up
from app.routes import bp as main_bp
app.register_blueprint(main_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
