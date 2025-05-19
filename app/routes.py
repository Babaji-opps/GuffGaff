import logging
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort, Blueprint
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import desc, and_

from app import db
from app.models import User, Conversation, Message, DailyChallenge, DailyCompletion, MovieSuggestion, Vote, ConversationType
from app.forms import SignupForm, LoginForm, NewConversationForm, MessageForm, DailyChallengeCompletionForm, MovieSuggestionForm

bp = Blueprint('main', __name__)

# Home page
@bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.conversations'))
    return render_template('home.html')

# Auth routes
@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.conversations'))
    
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('auth/signup.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.conversations'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash('Logged in successfully!', 'success')
            return redirect(next_page or url_for('main.conversations'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.login'))

# Conversation routes
@bp.route('/conversations')
@login_required
def conversations():
    # Show all users except the current user
    users = User.query.filter(User.id != current_user.id).order_by(User.username).all()
    # Show all group conversations the user is a member of
    group_conversations = current_user.conversations.filter_by(type=ConversationType.GROUP).order_by(Conversation.updated_at.desc()).all()
    return render_template('conversations/messenger.html', users=users, group_conversations=group_conversations, selected_user=None, selected_conversation=None, message_form=None)

@bp.route('/conversations/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def direct_message(user_id):
    other_user = User.query.get_or_404(user_id)
    if other_user.id == current_user.id:
        abort(404)
    # Find or create direct conversation
    from app.models import Conversation, ConversationType
    conversation = Conversation.query \
        .filter(Conversation.type == ConversationType.DIRECT) \
        .filter(Conversation.members.contains(current_user)) \
        .filter(Conversation.members.contains(other_user)) \
        .first()
    if not conversation:
        conversation = Conversation(type=ConversationType.DIRECT)
        conversation.members.append(current_user)
        conversation.members.append(other_user)
        db.session.add(conversation)
        db.session.commit()
    # Handle new message
    message_form = MessageForm()
    if message_form.validate_on_submit():
        content = message_form.content.data.strip()
        if content:
            message = Message(content=content, sender=current_user, conversation=conversation)
            db.session.add(message)
            db.session.commit()
            return redirect(url_for('main.direct_message', user_id=other_user.id))
    return render_template('conversations/messenger.html', users=User.query.filter(User.id != current_user.id).order_by(User.username).all(), selected_user=other_user, selected_conversation=conversation, message_form=message_form)

@bp.route('/conversations/group/<int:group_id>', methods=['GET', 'POST'])
@login_required
def group_conversation(group_id):
    conversation = Conversation.query.get_or_404(group_id)
    if conversation.type != ConversationType.GROUP or current_user not in conversation.members:
        abort(404)
    message_form = MessageForm()
    if message_form.validate_on_submit():
        content = message_form.content.data.strip()
        if content:
            message = Message(content=content, sender=current_user, conversation=conversation)
            db.session.add(message)
            db.session.commit()
            return redirect(url_for('main.group_conversation', group_id=group_id))
    users = User.query.filter(User.id != current_user.id).order_by(User.username).all()
    group_conversations = current_user.conversations.filter_by(type=ConversationType.GROUP).order_by(Conversation.updated_at.desc()).all()
    return render_template('conversations/messenger.html', users=users, group_conversations=group_conversations, selected_user=None, selected_conversation=conversation, message_form=message_form)

@bp.route('/conversations/group/<int:group_id>/add_members', methods=['GET', 'POST'])
@login_required
def add_group_members(group_id):
    conversation = Conversation.query.get_or_404(group_id)
    if conversation.type != ConversationType.GROUP or current_user not in conversation.members:
        abort(404)
    from app.forms import AddMembersForm
    form = AddMembersForm()
    # Only show users not already in the group
    existing_ids = [user.id for user in conversation.members]
    form.members.choices = [(user.id, user.username) for user in User.query.filter(User.id.notin_(existing_ids)).order_by(User.username).all()]
    if form.validate_on_submit():
        new_members = User.query.filter(User.id.in_(form.members.data)).all()
        for user in new_members:
            if user not in conversation.members:
                conversation.members.append(user)
        db.session.commit()
        flash('Members added to the group!', 'success')
        return redirect(url_for('main.group_conversation', group_id=group_id))
    return render_template('conversations/add_members.html', form=form, conversation=conversation)

# Daily challenge routes
@bp.route('/daily')
@login_required
def daily_challenge():
    today = datetime.now().date()
    challenge = DailyChallenge.query.filter_by(date=today).first()
    
    # If no challenge exists for today (unlikely due to our app.py setup)
    if not challenge:
        flash('No challenge available for today', 'info')
        return redirect(url_for('main.conversations'))
    
    # Check if user already completed this challenge
    completed = DailyCompletion.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge.id
    ).first() is not None
    
    form = DailyChallengeCompletionForm()
    form.challenge_id.data = challenge.id
    
    # Get recent completions by other users (for social motivation)
    recent_completions = DailyCompletion.query.filter_by(
        challenge_id=challenge.id
    ).join(User).filter(
        User.id != current_user.id
    ).order_by(
        DailyCompletion.created_at.desc()
    ).limit(5).all()
    
    return render_template('daily/index.html', 
                          challenge=challenge, 
                          completed=completed,
                          form=form,
                          recent_completions=recent_completions,
                          streak=current_user.get_streak())

@bp.route('/daily/complete', methods=['POST'])
@login_required
def complete_challenge():
    form = DailyChallengeCompletionForm()
    
    if form.validate_on_submit():
        challenge_id = form.challenge_id.data
        challenge = DailyChallenge.query.get_or_404(challenge_id)
        
        # Check if user already completed this challenge
        existing = DailyCompletion.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge.id
        ).first()
        
        if existing:
            flash('You have already completed this challenge!', 'warning')
        else:
            completion = DailyCompletion(
                completion_note=form.completion_note.data,
                user=current_user,
                challenge=challenge,
                date=challenge.date
            )
            db.session.add(completion)
            db.session.commit()
            flash('Challenge completed! Your streak continues!', 'success')
    
    return redirect(url_for('main.daily_challenge'))

# Movie suggestion routes
@bp.route('/conversations/<int:id>/movies/suggest', methods=['GET', 'POST'])
@login_required
def suggest_movie(id):
    conversation = Conversation.query.get_or_404(id)
    
    # Check if user is a member of this conversation
    if current_user not in conversation.members:
        abort(403)
    
    form = MovieSuggestionForm()
    
    if form.validate_on_submit():
        movie = MovieSuggestion(
            title=form.title.data,
            description=form.description.data,
            suggested_by=current_user,
            conversation=conversation
        )
        db.session.add(movie)
        db.session.commit()
        
        flash('Movie suggestion added!', 'success')
        return redirect(url_for('main.show_conversation', id=id))
    
    return render_template('movies/new.html', form=form, conversation=conversation)

@bp.route('/conversations/<int:conv_id>/movies/vote/<int:movie_id>', methods=['POST'])
@login_required
def vote_movie(conv_id, movie_id):
    conversation = Conversation.query.get_or_404(conv_id)
    movie = MovieSuggestion.query.get_or_404(movie_id)
    
    # Verify user is in conversation and movie belongs to this conversation
    if current_user not in conversation.members or movie.conversation_id != conv_id:
        abort(403)
    
    # Check if user already voted
    existing_vote = Vote.query.filter_by(
        user_id=current_user.id,
        movie_suggestion_id=movie_id
    ).first()
    
    if existing_vote:
        # Remove vote (toggle)
        db.session.delete(existing_vote)
        flash('Vote removed', 'info')
    else:
        # Add vote
        vote = Vote(user=current_user, movie_suggestion=movie)
        db.session.add(vote)
        flash('Vote added!', 'success')
    
    db.session.commit()
    return redirect(url_for('main.show_conversation', id=conv_id))

# User profile
@bp.route('/profile')
@login_required
def profile():
    # Get user's challenge streak
    streak = current_user.get_streak()
    
    # Get recent completions
    recent_completions = DailyCompletion.query.filter_by(
        user_id=current_user.id
    ).order_by(
        DailyCompletion.date.desc()
    ).limit(10).all()
    
    # Get user's suggested movies
    suggested_movies = MovieSuggestion.query.filter_by(
        suggested_by_id=current_user.id
    ).order_by(
        MovieSuggestion.created_at.desc()
    ).limit(5).all()
    
    return render_template('profile/index.html', 
                          user=current_user,
                          streak=streak,
                          recent_completions=recent_completions,
                          suggested_movies=suggested_movies)

@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    from app.forms import ProfileUpdateForm
    form = ProfileUpdateForm(obj=current_user)
    if form.validate_on_submit():
        # Update username if changed (no password required)
        if form.username.data != current_user.username:
            current_user.username = form.username.data
            flash('Username updated successfully.', 'success')
        # Update email if changed (require current password)
        if form.email.data != current_user.email:
            if not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect. Email not updated.', 'danger')
                return render_template('profile/edit.html', form=form)
            current_user.email = form.email.data
            flash('Email updated successfully.', 'success')
        # Update password if provided
        if form.new_password.data:
            current_user.set_password(form.new_password.data)
            flash('Password updated successfully.', 'success')
        db.session.commit()
        return redirect(url_for('main.profile'))
    return render_template('profile/edit.html', form=form)

# Error handlers
@bp.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@bp.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@bp.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500
