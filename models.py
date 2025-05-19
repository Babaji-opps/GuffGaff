from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)  # Format: HH:MM
    end_time = db.Column(db.String(5), nullable=False)  # Format: HH:MM
    description = db.Column(db.String(500), nullable=True)
    icon = db.Column(db.String(100), nullable=False)
    reminder = db.Column(db.Boolean, default=False)
    day = db.Column(db.String(10), nullable=False)
    progress = db.Column(db.Integer, default=0)  # A field for task progress
    completed = db.Column(db.Boolean, default=False)

    def mark_complete(self):
        self.completed = True

    def update_progress(self, value):
        self.progress = value
