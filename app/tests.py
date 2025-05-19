import os
import unittest
from datetime import datetime, date
from flask_login import current_user
from werkzeug.security import generate_password_hash

from app import app, db
from models import User, Conversation, Message, DailyChallenge, DailyCompletion, MovieSuggestion, Vote, ConversationType

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create tables and initial test data
        db.create_all()
        self.create_test_data()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def create_test_data(self):
        # Create test users
        user1 = User(username='testuser1', email='test1@example.com')
        user1.set_password('password')
        
        user2 = User(username='testuser2', email='test2@example.com')
        user2.set_password('password')
        
        # Create a daily challenge
        challenge = DailyChallenge(
            title='Test Challenge',
            description='This is a test challenge',
            date=date.today()
        )
        
        db.session.add_all([user1, user2, challenge])
        db.session.commit()
    
    def login(self, email='test1@example.com', password='password'):
        return self.app.post('/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)
    
    def logout(self):
        return self.app.get('/logout', follow_redirects=True)
    
    # Tests for routes
    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Connect, Challenge, Chat', response.data)
    
    def test_signup_page(self):
        response = self.app.get('/signup')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create Account', response.data)
    
    def test_login_page(self):
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Log In', response.data)
    
    def test_signup_user(self):
        response = self.app.post('/signup', data=dict(
            username='newuser',
            email='new@example.com',
            password='password123',
            confirm_password='password123'
        ), follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(email='new@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'newuser')
    
    def test_login_logout(self):
        # Test login
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged in successfully', response.data)
        
        # Test logout
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have been logged out', response.data)
    
    def test_invalid_login(self):
        response = self.login(email='wrong@example.com', password='wrongpass')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email or password', response.data)
    
    def test_conversations_route_requires_login(self):
        response = self.app.get('/conversations', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please log in to access this page', response.data)
    
    def test_view_conversations(self):
        self.login()
        response = self.app.get('/conversations')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Your Conversations', response.data)
    
    def test_daily_challenge_route(self):
        self.login()
        response = self.app.get('/daily')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Challenge', response.data)
    
    def test_complete_challenge(self):
        self.login()
        user = User.query.filter_by(email='test1@example.com').first()
        challenge = DailyChallenge.query.filter_by(title='Test Challenge').first()
        
        response = self.app.post('/daily/complete', data=dict(
            challenge_id=challenge.id,
            completion_note='Completed test challenge'
        ), follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Challenge completed', response.data)
        
        # Verify completion was recorded
        completion = DailyCompletion.query.filter_by(
            user_id=user.id,
            challenge_id=challenge.id
        ).first()
        
        self.assertIsNotNone(completion)
        self.assertEqual(completion.completion_note, 'Completed test challenge')
    
    def test_profile_route(self):
        self.login()
        response = self.app.get('/profile')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Challenge History', response.data)
        self.assertIn(b'testuser1', response.data)

if __name__ == '__main__':
    unittest.main()
