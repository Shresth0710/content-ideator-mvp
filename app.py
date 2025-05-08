#!/usr/bin/env python3
import sqlite3
import random
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)
DATABASE = 'submissions.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Create a new connection to the database
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    """Create the submissions table if it doesn't exist."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                ideas TEXT
            )
        ''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection on teardown."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def generate_content_ideas(keyword):
    """
    Generate 10 dummy content ideas based on the provided keyword.
    This is a basic simulation – in a real world scenario, you could integrate
    with an AI service (while ensuring cost-free usage).
    """
    ideas = []
    formats = [
        "How to master {}",
        "10 surprising facts about {}",
        "The ultimate guide to {}",
        "{}: Tips and Tricks",
        "The history of {} explained",
        "Why {} is the future",
        "Exploring the benefits of {}",
        "Common myths about {} debunked",
        "Expert insight on {}",
        "{} in 2025: What to expect"
    ]
    for fmt in formats:
        ideas.append(fmt.format(keyword))
    # Shuffle ideas for variety
    random.shuffle(ideas)
    return ideas

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keyword = request.form.get('keyword', '').strip()
        if keyword:
            ideas = generate_content_ideas(keyword)
            # Convert list of ideas to a string with a separator (you can also use JSON)
            ideas_str = "||".join(ideas)
            # Save to database
            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO submissions (keyword, ideas) VALUES (?, ?)", (keyword, ideas_str))
            db.commit()
            # Redirect to result page with the ID of the submission
            submission_id = cursor.lastrowid
            return redirect(url_for('result', submission_id=submission_id))
    return render_template('index.html')

@app.route('/result/<int:submission_id>')
def result(submission_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT keyword, ideas FROM submissions WHERE id = ?", (submission_id,))
    row = cursor.fetchone()
    if row:
        keyword, ideas_str = row
        ideas = ideas_str.split("||")
        return render_template('result.html', keyword=keyword, ideas=ideas)
    return "Submission not found", 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)