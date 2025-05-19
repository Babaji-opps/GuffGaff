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
    user_conversations = current_user.conversations.order_by(desc(Conversation.updated_at)).all()
    # Use the new WhatsApp/Telegram style messenger template
    return render_template('conversations/messenger.html', conversations=user_conversations, selected_conversation=None, message_form=None)

@bp.route('/conversations/new', methods=['GET', 'POST'])
@login_required
def new_conversation():
    form = NewConversationForm()
    # Get all users except current user for the form choices
    form.members.choices = [(user.id, user.username) 
                           for user in User.query.filter(User.id != current_user.id).all()]
    
    if form.validate_on_submit():
        selected_members = User.query.filter(User.id.in_(form.members.data)).all()
        
        # Determine conversation type based on number of members
        conv_type = ConversationType.GROUP if len(selected_members) > 1 else ConversationType.DIRECT
        
        # For direct messages, check if a conversation already exists between these two users
        if conv_type == ConversationType.DIRECT and len(selected_members) == 1:
            other_user = selected_members[0]
            
            # Find existing direct conversations between these two users
            existing_conversation = Conversation.query.filter(
                Conversation.type == ConversationType.DIRECT,
                Conversation.members.contains(current_user),
                Conversation.members.contains(other_user)
            ).first()
            
            if existing_conversation:
                flash('Continuing existing conversation', 'info')
                return redirect(url_for('show_conversation', id=existing_conversation.id))
        
        # Create new conversation
        conversation = Conversation(
            title=form.title.data if form.title.data else None,
            type=conv_type
        )
        
        # Add current user and selected members
        conversation.members.append(current_user)
        for member in selected_members:
            conversation.members.append(member)
        
        # For group chats without a title, generate one based on member names
        if conv_type == ConversationType.GROUP and not conversation.title:
            member_names = [member.username for member in selected_members[:3]]
            if len(selected_members) > 3:
                conversation.title = f"{', '.join(member_names)} and {len(selected_members) - 3} others"
            else:
                conversation.title = f"{', '.join(member_names)} group"
        
        db.session.add(conversation)
        db.session.commit()
        
        # Create a welcome message for new conversations
        welcome_msg = "Conversation started! 👋"
        if conv_type == ConversationType.GROUP:
            welcome_msg = f"Group chat created by {current_user.username}! 👋"
        
        system_message = Message(
            content=welcome_msg,
            sender=current_user,
            conversation=conversation
        )
        db.session.add(system_message)
        db.session.commit()
        
        flash('Conversation created!', 'success')
        return redirect(url_for('show_conversation', id=conversation.id))
    
    return render_template('conversations/new.html', form=form)

@bp.route('/conversations/<int:id>', methods=['GET', 'POST'])
@login_required
def show_conversation(id):
    conversation = Conversation.query.get_or_404(id)
    
    # Check if user is a member of this conversation
    if current_user not in conversation.members:
        abort(403)
    
    # Mark user as having seen this conversation (for read receipts in future)
    conversation.updated_at = datetime.utcnow()
    
    # Handle new messages
    message_form = MessageForm()
    if message_form.validate_on_submit():
        # Don't save empty messages
        message_content = message_form.content.data
        if message_content and message_content.strip():
            message = Message(
                content=message_content.strip(),
                sender=current_user,
                conversation=conversation
            )
            db.session.add(message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            
            db.session.commit()
        
        # Clear form and redirect to same page (to avoid form resubmission)
        return redirect(url_for('show_conversation', id=id))
    
    # Get movie suggestions for this conversation
    movie_suggestions = conversation.movie_suggestions.all()
    
    # Check which movies the current user has voted for
    voted_movie_ids = [vote.movie_suggestion_id for vote in 
                      Vote.query.filter_by(user_id=current_user.id).all()]
    
    # Get other conversations for the sidebar
    other_conversations = current_user.conversations.filter(Conversation.id != id).order_by(
        desc(Conversation.updated_at)).limit(5).all()
    
    # Get all conversations for the sidebar
    all_conversations = current_user.conversations.order_by(desc(Conversation.updated_at)).all()
    
    # Use the new WhatsApp/Telegram style messenger template
    return render_template('conversations/messenger.html', 
                          conversations=all_conversations,
                          selected_conversation=conversation,
                          message_form=message_form,
                          movie_suggestions=movie_suggestions,
                          voted_movie_ids=voted_movie_ids)

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
    
    return redirect(url_for('daily_challenge'))

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
        return redirect(url_for('show_conversation', id=id))
    
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
    return redirect(url_for('show_conversation', id=conv_id))

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
