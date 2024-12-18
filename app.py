from flask import Flask, render_template, request, jsonify, session, flash
import sqlite3
import requests

def getuserdata():
    cnt = sqlite3.connect("studentData.db")
    cursor = cnt.cursor()

    # Fetch all data from the 'data' table
    cursor.execute("SELECT * FROM data order by score DESC")
    users = cursor.fetchall()
    cnt.close()

    # Pass the fetched data to the template
    return users

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # This is for session management, required for tracking logged-in users

@app.route("/")
def index():
    return render_template("login.html")


@app.route("/index")
def main_page():
    return render_template("index.html",users = getuserdata())




@app.route("/quiz")
def quiz():
    return render_template("quiz.html")

@app.route("/submit_score", methods=['POST'])
def submit_score():
    # Get the score from the request
    data = request.get_json()
    score = data.get('score')

    # Assuming that the username is stored in the session after login
    username = session.get('username')

    if username is None:
        return render_template("index.html",error="User not logged in")

    # Connect to the database
    cnt = sqlite3.connect("studentData.db")
    cursor = cnt.cursor()

    # Update score in the database for the logged-in user
    cursor.execute("UPDATE data SET score = ? WHERE username = ?", (score, username))
    cnt.commit()
    cnt.close()

    # Respond with success
    return jsonify({"message": "Score submitted successfully", "score": score})

@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["uname"]
    password = request.form["psw"]
    password2 = request.form["psw2"]
    if password != password2:
        return render_template("login.html",error = "Password mismatched")
    email = request.form["email"]

    # Connect to the database
    cnt = sqlite3.connect("studentData.db")
    cursor = cnt.cursor()
    query = "SELECT * FROM data WHERE username = ?"
    cursor.execute(query, (username,))
    checkUser = cursor.fetchone()
    if checkUser:
        error = "Username Already Exists"
        flash(error)
        return render_template("login.html",error = error)
    # Get the last used ID for inserting a new record
    cursor.execute("SELECT COUNT(id) FROM data")
    last_id = cursor.fetchone()

    # Insert new user data into the database
    cursor.execute(
        "INSERT INTO data (id, username, email, password, score) VALUES (?, ?, ?, ?, ?)",
        (last_id[0] + 1, username, email, password, None)  # Assuming last_id[0] is the current row count
    )

    # Commit and close the database connection
    cnt.commit()
    cnt.close()

    # Store username in session after signup/login for tracking
    session['username'] = username

    # Redirect to the quiz page or return a success message
    return render_template("index.html",users = getuserdata())

@app.route("/login", methods=["POST"])
def login():
    username = request.form["uname"]
    password = request.form["psw"]

    # Connect to the database
    cnt = sqlite3.connect("studentData.db")
    cursor = cnt.cursor()

    # Verify the user exists in the database
    cursor.execute("SELECT * FROM data WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()

    if user:
        # Store username in session after successful login
        session['username'] = username
        return render_template("index.html",users = getuserdata())
    else:
        error = "Invalid username or password"
        flash(error)
        return render_template("login.html",error = error)

@app.route("/fetch_quiz_questions", methods=['GET'])
def fetch_quiz_questions():
    # Fetch quiz questions from OpenTDB API
    response = requests.get('https://opentdb.com/api.php?amount=10&category=18&difficulty=easy&type=multiple')
    data = response.json()

    # Parse the questions into the desired format
    quiz_questions = []
    for item in data['results']:
        question = {
            'question': item['question'],
            'a': item['incorrect_answers'][0],
            'b': item['incorrect_answers'][1],
            'c': item['incorrect_answers'][2],
            'd': item['correct_answer'],
            'correct': 'd'  # Assuming the correct answer is always 'd'
        }
        quiz_questions.append(question)

    return jsonify(quiz_questions)

if __name__ == "__main__":
    app.run(debug=True)
