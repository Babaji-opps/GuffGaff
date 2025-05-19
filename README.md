# GuffGaff - Social Challenge & Chat App

GuffGaff is a feature-rich social platform that combines messaging, daily challenges, and movie planning in one seamless application. Built with Flask, it offers a modern, WhatsApp/Telegram-inspired interface focused on social interaction and engagement.

---

## 🚀 Features

### Conversations
- **Direct Messaging:** Private one-on-one conversations
- **Group Chats:** Create group conversations with multiple participants
- **Rich Message Interface:** Modern chat bubbles and timestamps
- **Message History:** Full conversation history

### Daily Challenges
- **Daily Activity Tasks:** New challenges posted every day
- **Challenge Completion:** Mark challenges as complete with optional notes
- **Streak Tracking:** Monitor consecutive days of completed challenges
- **Community Engagement:** See which friends have completed challenges

### Movie Planning
- **Movie Suggestions:** Suggest movies to watch with friends
- **Voting System:** Vote on favorite movie suggestions
- **Description Support:** Add context to your movie suggestions
- **Group Decision Making:** Easily see the most popular choices

---

## 🛠️ Technology Stack
- **Backend:** Flask (Python)
- **Database:** PostgreSQL (production) / SQLite (development)
- **ORM:** SQLAlchemy
- **Forms:** WTForms with Flask-WTF
- **Authentication:** Flask-Login
- **Frontend:** Bootstrap CSS with custom styling
- **Deployment:** Gunicorn WSGI server

---

## 🌟 Key Features Overview
- **User System & Authentication:** Secure sign up, login, and session management
- **Social Challenges:** Create, join, and track daily/weekly challenges
- **Movie Night Planner:** Schedule, suggest, and vote on movies
- **Chat System:** One-on-one and group messaging
- **Dashboard & Activity Feed:** Track progress, challenges, and messages

---

## 🚧 Future Enhancements
- Friend system or follower model
- Leaderboards and badges
- Post reactions and comments
- Real-time chat (WebSockets)
- Voice/video calling
- Push notifications
- AI-based challenge recommendations
- Admin panel for moderation

---

## 👥 Audience
- Students seeking motivation and consistency
- Friends wanting a central virtual hangout
- Anyone looking for a lightweight, social productivity platform

---

## 🙌 Made With
- ❤️ by a Computer Science student
- 🧠 Inspired by Discord, Habitica, and Duolingo

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip
- Git
- (Recommended) Virtualenv

### Installation
```sh
git clone https://github.com/YogiSunil/GuffGaff.git
cd GuffGaff
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

### Environment Setup
Create a `.env` file in the root directory:
```
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///guffgaff.db
```

### Database Initialization
```sh
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Run the Development Server
```sh
flask run
```
Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) to explore GuffGaff!

---

## 🌐 Deployment (Heroku Example)
```sh
heroku login
heroku create guffgaff
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
heroku config:set FLASK_APP=app FLASK_ENV=production SECRET_KEY=your_secret_key
heroku run flask db upgrade
heroku open
```

---

## 📄 License
MIT License

---

Enjoy using **GuffGaff** and make your daily life more engaging, social, and fun!
