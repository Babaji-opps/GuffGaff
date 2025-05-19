import enum
from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import func
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

# Association tables for many-to-many relationships
conversation_users = db.Table('conversation_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('conversation_id', db.Integer, db.ForeignKey('conversation.id'), primary_key=True)
)

class ConversationType(enum.Enum):
    DIRECT = 'direct'
    GROUP = 'group'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('Message', back_populates='sender', lazy='dynamic')
    conversations = db.relationship('Conversation', secondary=conversation_users, 
                                   back_populates='members', lazy='dynamic')
    daily_completions = db.relationship('DailyCompletion', back_populates='user', lazy='dynamic')
    movie_suggestions = db.relationship('MovieSuggestion', back_populates='suggested_by', lazy='dynamic')
    votes = db.relationship('Vote', back_populates='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_streak(self):
        """Calculate the user's current streak of completed daily challenges"""
        completions = DailyCompletion.query.filter_by(user_id=self.id).order_by(DailyCompletion.date.desc()).all()
        if not completions:
            return 0
        
        streak = 1
        latest_date = completions[0].date
        
        for i in range(1, len(completions)):
            if (latest_date - completions[i].date).days == 1:
                streak += 1
                latest_date = completions[i].date
            else:
                break
        
        return streak

    def __repr__(self):
        return f'<User {self.username}>'

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    type = db.Column(db.Enum(ConversationType))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = db.relationship('User', secondary=conversation_users, 
                            back_populates='conversations', lazy='joined')
    messages = db.relationship('Message', back_populates='conversation', lazy='dynamic',
                             order_by='Message.created_at.asc()')
    movie_suggestions = db.relationship('MovieSuggestion', back_populates='conversation', lazy='dynamic',
                                     order_by='MovieSuggestion.created_at.desc()')
    
    def get_display_name(self, current_user_id):
        """Get a display name for the conversation based on type and members"""
        if self.title:
            return self.title
        
        if self.type == ConversationType.DIRECT:
            # For direct messages, show the other user's name
            other_user = next((user for user in self.members if user.id != current_user_id), None)
            return other_user.username if other_user else "Chat"
        
        # For groups without titles, list first few members
        member_names = [user.username for user in self.members if user.id != current_user_id]
        if len(member_names) <= 2:
            return ", ".join(member_names)
        return f"{', '.join(member_names[:2])} and {len(member_names) - 2} others"
    
    def __repr__(self):
        return f'<Conversation {self.id}: {self.type.value}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    
    # Relationships
    sender = db.relationship('User', back_populates='messages')
    conversation = db.relationship('Conversation', back_populates='messages')
    
    def __repr__(self):
        return f'<Message {self.id} by {self.sender_id}>'

class DailyChallenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False, unique=True, default=datetime.utcnow().date)
    
    # Relationships
    completions = db.relationship('DailyCompletion', back_populates='challenge', lazy='dynamic')
    
    def __repr__(self):
        return f'<DailyChallenge {self.id}: {self.title}>'

class DailyCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    completion_note = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('daily_challenge.id'), nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='daily_completions')
    challenge = db.relationship('DailyChallenge', back_populates='completions')
    
    # Unique constraint to ensure a user can only complete a challenge once
    __table_args__ = (db.UniqueConstraint('user_id', 'challenge_id', name='_user_challenge_uc'),)
    
    def __repr__(self):
        return f'<DailyCompletion {self.id} by {self.user_id}'

class MovieSuggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    suggested_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    
    # Relationships
    suggested_by = db.relationship('User', back_populates='movie_suggestions')
    conversation = db.relationship('Conversation', back_populates='movie_suggestions')
    votes = db.relationship('Vote', back_populates='movie_suggestion', lazy='dynamic')
    
    def vote_count(self):
        """Get the total number of votes for this movie suggestion"""
        return self.votes.count()
    
    def __repr__(self):
        return f'<MovieSuggestion {self.id}: {self.title}>'

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_suggestion_id = db.Column(db.Integer, db.ForeignKey('movie_suggestion.id'), nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='votes')
    movie_suggestion = db.relationship('MovieSuggestion', back_populates='votes')
    
    # Unique constraint to ensure a user can only vote once per movie suggestion
    __table_args__ = (db.UniqueConstraint('user_id', 'movie_suggestion_id', name='_user_movie_uc'),)
    
    def __repr__(self):
        return f'<Vote {self.id} by {self.user_id}>'
