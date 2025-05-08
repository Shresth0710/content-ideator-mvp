import os
import sqlite3
import random
from flask import Flask, render_template, request, redirect, url_for, g
from transformers import pipeline

# Initialize the Hugging Face text-generation pipeline
llm_pipeline = pipeline("text-generation", model="distilgpt2")

# Configure the Flask app; note the template_folder is one level up
app = Flask(__name__, template_folder="../templates")

# Use /tmp for the SQLite DB as it is writable in Vercel’s environment.
DATABASE = os.environ.get("DATABASE_PATH", "/tmp/submissions.db")

def get_db():
    if not hasattr(g, '_database'):
        g._database = sqlite3.connect(DATABASE)
    return g._database

def init_db():
    db = get_db()
    cursor = db.cursor()
    # Create table with an additional column for LLM generated output
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT,
            ideas TEXT,
            llm_output TEXT
        )
    """)
    db.commit()

@app.before_request
def before_request():
    init_db()

@app.teardown_appcontext
def close_connection(exception):
    if hasattr(g, '_database'):
        g._database.close()

def generate_content_ideas(keyword):
    """
    Generate 10 dummy content ideas using simple templates.
    """
    ideas = []
    templates_list = [
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
    for fmt in templates_list:
        ideas.append(fmt.format(keyword))
    random.shuffle(ideas)
    return ideas

def generate_llm_output(keyword):
    """
    Use the Hugging Face LLM (distilgpt2) to generate additional creative text
    based on the provided keyword.
    """
    prompt = f"Generate a creative and engaging content idea about {keyword}: "
    # Limit the output length to 50 tokens for faster responses
    output = llm_pipeline(prompt, max_length=50, do_sample=True, top_k=50)[0]["generated_text"]
    return output

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        if keyword:
            ideas = generate_content_ideas(keyword)
            llm_output = generate_llm_output(keyword)
            ideas_str = "||".join(ideas)
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO submissions (keyword, ideas, llm_output) VALUES (?, ?, ?)",
                (keyword, ideas_str, llm_output)
            )
            db.commit()
            submission_id = cursor.lastrowid
            return redirect(url_for("result", submission_id=submission_id))
    return render_template("index.html")

@app.route("/result/<int:submission_id>")
def result(submission_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT keyword, ideas, llm_output FROM submissions WHERE id = ?",
        (submission_id,)
    )
    row = cursor.fetchone()
    if row:
        keyword, ideas_str, llm_output = row
        ideas = ideas_str.split("||")
        return render_template("result.html", keyword=keyword, ideas=ideas, llm_output=llm_output)
    return "Submission not found", 404

if __name__ == "__main__":
    init_db()
    app.run(debug=True)