import logging
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import desc, and_

from app import app, db
from models import User, Conversation, Message, DailyChallenge, DailyCompletion, MovieSuggestion, Vote, ConversationType
from forms import SignupForm, LoginForm, NewConversationForm, MessageForm, DailyChallengeCompletionForm, MovieSuggestionForm

# Home page
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('conversations'))
    return render_template('home.html')

# Auth routes
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('conversations'))
    
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('conversations'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash('Logged in successfully!', 'success')
            return redirect(next_page or url_for('conversations'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Conversation routes
@app.route('/conversations')
@login_required
def conversations():
    user_conversations = current_user.conversations.order_by(desc(Conversation.updated_at)).all()
    return render_template('conversations/index.html', conversations=user_conversations)

@app.route('/conversations/new', methods=['GET', 'POST'])
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
        
        # Create new conversation
        conversation = Conversation(
            title=form.title.data if form.title.data else None,
            type=conv_type
        )
        
        # Add current user and selected members
        conversation.members.append(current_user)
        for member in selected_members:
            conversation.members.append(member)
        
        db.session.add(conversation)
        db.session.commit()
        
        flash('Conversation created!', 'success')
        return redirect(url_for('show_conversation', id=conversation.id))
    
    return render_template('conversations/new.html', form=form)

@app.route('/conversations/<int:id>', methods=['GET', 'POST'])
@login_required
def show_conversation(id):
    conversation = Conversation.query.get_or_404(id)
    
    # Check if user is a member of this conversation
    if current_user not in conversation.members:
        abort(403)
    
    # Handle new messages
    message_form = MessageForm()
    if message_form.validate_on_submit():
        message = Message(
            content=message_form.content.data,
            sender=current_user,
            conversation=conversation
        )
        db.session.add(message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Clear form and redirect to same page (to avoid form resubmission)
        message_form.content.data = ''
        return redirect(url_for('show_conversation', id=id))
    
    # Get movie suggestions for this conversation
    movie_suggestions = conversation.movie_suggestions.all()
    
    # Check which movies the current user has voted for
    voted_movie_ids = [vote.movie_suggestion_id for vote in 
                      Vote.query.filter_by(user_id=current_user.id).all()]
    
    return render_template('conversations/show.html', 
                          conversation=conversation,
                          message_form=message_form,
                          movie_suggestions=movie_suggestions,
                          voted_movie_ids=voted_movie_ids)

# Daily challenge routes
@app.route('/daily')
@login_required
def daily_challenge():
    today = datetime.now().date()
    challenge = DailyChallenge.query.filter_by(date=today).first()
    
    # If no challenge exists for today (unlikely due to our app.py setup)
    if not challenge:
        flash('No challenge available for today', 'info')
        return redirect(url_for('conversations'))
    
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

@app.route('/daily/complete', methods=['POST'])
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
@app.route('/conversations/<int:id>/movies/suggest', methods=['GET', 'POST'])
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

@app.route('/conversations/<int:conv_id>/movies/vote/<int:movie_id>', methods=['POST'])
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
@app.route('/profile')
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
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500
