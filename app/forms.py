from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address'),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one or log in.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class NewConversationForm(FlaskForm):
    title = StringField('Group Name (optional)', validators=[Length(max=128)])
    members = SelectMultipleField('Select Members', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create Chat')

class MessageForm(FlaskForm):
    content = TextAreaField('Message', validators=[DataRequired(message="Message cannot be empty")])
    submit = SubmitField('Send')

class DailyChallengeCompletionForm(FlaskForm):
    completion_note = TextAreaField('How did you complete the challenge? (optional)', validators=[Length(max=500)])
    submit = SubmitField('Mark as Completed')
    challenge_id = HiddenField('Challenge ID', validators=[DataRequired()])

class MovieSuggestionForm(FlaskForm):
    title = StringField('Movie Title', validators=[
        DataRequired(),
        Length(min=1, max=200, message='Title must be between 1 and 200 characters')
    ])
    description = TextAreaField('Description (optional)', validators=[Length(max=1000)])
    submit = SubmitField('Suggest Movie')
