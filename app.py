from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from models import db, Schedule
from flask_migrate import Migrate


import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schedules.db'  # Using SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)


@app.route('/')
def index():
    schedules = Schedule.query.all()  # Fetch all schedules from the database
    # Fetch the completed tasks by filtering on the 'completed' field (not 'status')
    completed_tasks = Schedule.query.filter_by(completed=True).all()
    completed_progress = sum([task.progress for task in completed_tasks])
    total_tasks = len(schedules)
    progress_percentage = (completed_progress / (total_tasks * 100)) * 100 if total_tasks > 0 else 0
    return render_template('index.html', schedules=schedules, progress_percentage=progress_percentage)

@app.route('/schedules/create', methods=['GET', 'POST'])
def create_schedule():
    if request.method == 'POST':
        date = request.form['date']
        day = datetime.strptime(date, '%Y-%m-%d').strftime('%A')  # Get day of the week
        new_schedule = Schedule(
            title=request.form['title'],
            date=date,
            time=request.form['time'],
            description=request.form['description'],
            icon=request.form['icon'],
            reminder='reminder' in request.form,
            day=day
        )
        db.session.add(new_schedule)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create_schedule.html')

@app.route('/schedules/edit/<int:schedule_id>', methods=['GET', 'POST'])
def edit_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if request.method == 'POST':
        schedule.title = request.form['title']
        schedule.date = request.form['date']
        schedule.time = request.form['time']
        schedule.description = request.form['description']
        schedule.icon = request.form['icon']
        schedule.reminder = 'reminder' in request.form
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit_schedule.html', schedule=schedule)

@app.route('/schedules/delete/<int:schedule_id>', methods=['POST'])
def delete_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/schedules/move/<int:schedule_id>', methods=['POST'])
def move_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    data = request.get_json()
    new_day = data['new_day']  # Get the new day from the JSON data
    schedule.day = new_day
    db.session.commit()
    return '', 204  # No content response to indicate successful move


@app.route('/schedules/complete/<int:schedule_id>', methods=['POST'])
def complete_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    schedule.mark_complete()
    db.session.commit()  # Ensure the commit happens
    return redirect(url_for('index'))

@app.route('/schedules/update-progress/<int:schedule_id>', methods=['POST'])
def update_progress(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    progress_value = int(request.form['progress'])  # Progress value sent from the client-side
    schedule.update_progress(progress_value)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
