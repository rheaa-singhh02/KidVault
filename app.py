import os
import random
import uuid
from datetime import datetime
from functools import wraps

import pymysql
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "kidvault-dev-secret")


def get_db_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "Namu@1820"),
        database=os.getenv("MYSQL_DATABASE", "quiz"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def init_db():
    statements = [
        """
        CREATE TABLE IF NOT EXISTS parents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS kids (
            id INT AUTO_INCREMENT PRIMARY KEY,
            parent_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            class_level VARCHAR(20) NOT NULL,
            upi_id VARCHAR(255) DEFAULT NULL,
            wallet_balance DECIMAL(10, 2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES parents(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS quizzes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            parent_id INT NOT NULL,
            kid_id INT NOT NULL,
            subject VARCHAR(50) NOT NULL,
            reward_amount DECIMAL(10, 2) NOT NULL,
            launch_token VARCHAR(64) NOT NULL UNIQUE,
            status VARCHAR(30) DEFAULT 'launched',
            total_questions INT DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES parents(id) ON DELETE CASCADE,
            FOREIGN KEY (kid_id) REFERENCES kids(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            quiz_id INT NOT NULL,
            question_text TEXT NOT NULL,
            option_a VARCHAR(255) NOT NULL,
            option_b VARCHAR(255) NOT NULL,
            option_c VARCHAR(255) NOT NULL,
            option_d VARCHAR(255) NOT NULL,
            correct_option CHAR(1) NOT NULL,
            question_order INT NOT NULL,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            quiz_id INT NOT NULL UNIQUE,
            score INT NOT NULL,
            passed TINYINT(1) NOT NULL DEFAULT 0,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS reward_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            quiz_id INT NOT NULL UNIQUE,
            kid_id INT NOT NULL,
            requested_amount DECIMAL(10, 2) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at DATETIME DEFAULT NULL,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
            FOREIGN KEY (kid_id) REFERENCES kids(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS wallet_transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            kid_id INT NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            type VARCHAR(20) NOT NULL,
            note VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (kid_id) REFERENCES kids(id) ON DELETE CASCADE
        )
        """,
    ]

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
            cursor.execute("SELECT id FROM parents WHERE email = %s", ("parent@kidvault.com",))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO parents (email, password) VALUES (%s, %s)",
                    ("parent@kidvault.com", "kidvault123"),
                )
        connection.commit()
    finally:
        connection.close()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "parent_id" not in session:
            return redirect(url_for("index"))
        return view(*args, **kwargs)

    return wrapped_view


QUESTION_BANK = {
    "maths": {
        "1-3": [
            ("What is 7 + 5?", ["10", "11", "12", "13"], "C"),
            ("Which number is bigger?", ["19", "14", "11", "9"], "A"),
            ("What is 15 - 6?", ["8", "9", "10", "11"], "B"),
            ("How many sides does a triangle have?", ["2", "3", "4", "5"], "B"),
            ("What comes next: 2, 4, 6, ?", ["7", "8", "9", "10"], "B"),
            ("What is 3 x 4?", ["7", "10", "12", "14"], "C"),
            ("Half of 10 is?", ["3", "4", "5", "6"], "C"),
        ],
        "4-6": [
            ("What is 36 / 6?", ["5", "6", "7", "8"], "B"),
            ("What is 14 x 3?", ["42", "38", "44", "40"], "A"),
            ("What is the perimeter of a square with side 5?", ["10", "15", "20", "25"], "C"),
            ("Which is a prime number?", ["9", "15", "17", "21"], "C"),
            ("What is 3/4 of 20?", ["12", "14", "15", "16"], "C"),
            ("What is 125 - 48?", ["67", "77", "87", "97"], "B"),
            ("Convert 2.5 to a fraction.", ["1/2", "5/2", "2/5", "25/10"], "B"),
        ],
        "7-9": [
            ("Solve: 2x + 6 = 18", ["4", "5", "6", "7"], "C"),
            ("What is 15% of 200?", ["20", "25", "30", "35"], "C"),
            ("Simplify: 3^2 + 4^2", ["12", "25", "49", "81"], "B"),
            ("What is the area of a rectangle 8 by 6?", ["14", "28", "42", "48"], "D"),
            ("If a:b = 2:3 and a = 10, b = ?", ["12", "15", "18", "20"], "B"),
            ("What is the square root of 169?", ["11", "12", "13", "14"], "C"),
            ("Solve: 5(2 + 3)", ["10", "15", "20", "25"], "D"),
        ],
        "10-12": [
            ("Solve: 3x - 7 = 20", ["7", "8", "9", "10"], "C"),
            ("What is sin 90 degrees?", ["0", "1/2", "1", "sqrt(2)"], "C"),
            ("Derivative of x^2 is?", ["x", "2x", "x^2", "2"], "B"),
            ("What is the quadratic formula used for?", ["Ratios", "Triangles", "Equations", "Probability"], "C"),
            ("What is log10(100)?", ["1", "2", "10", "100"], "B"),
            ("What is the midpoint of 2 and 10?", ["4", "5", "6", "7"], "C"),
            ("If the probability of success is 0.2, probability of failure is?", ["0.2", "0.5", "0.8", "1.2"], "C"),
        ],
    },
    "science": {
        "1-3": [
            ("Which planet do we live on?", ["Mars", "Earth", "Venus", "Jupiter"], "B"),
            ("Plants need this gas from air.", ["Carbon dioxide", "Oxygen", "Nitrogen", "Helium"], "A"),
            ("How many legs does an insect usually have?", ["4", "6", "8", "10"], "B"),
            ("Water turns into ice when it becomes?", ["Hot", "Cold", "Sweet", "Heavy"], "B"),
            ("Which sense organ helps us hear?", ["Eyes", "Ears", "Nose", "Hands"], "B"),
            ("The sun gives us?", ["Rain", "Light and heat", "Snow", "Wind"], "B"),
            ("Which animal lives in water?", ["Camel", "Fish", "Tiger", "Dog"], "B"),
        ],
        "4-6": [
            ("Which part of the plant makes food?", ["Root", "Stem", "Leaf", "Flower"], "C"),
            ("The process of water changing into vapor is called?", ["Melting", "Evaporation", "Freezing", "Condensation"], "B"),
            ("Humans have how many permanent teeth?", ["20", "24", "28", "32"], "D"),
            ("Which organ pumps blood?", ["Lungs", "Brain", "Heart", "Liver"], "C"),
            ("Earth revolves around the?", ["Moon", "Mars", "Sun", "Stars"], "C"),
            ("Which is a conductor of electricity?", ["Rubber", "Plastic", "Copper", "Wood"], "C"),
            ("Force that pulls objects down is?", ["Magnetism", "Gravity", "Friction", "Energy"], "B"),
        ],
        "7-9": [
            ("Unit of electric current is?", ["Volt", "Ampere", "Ohm", "Watt"], "B"),
            ("Cell division helps in?", ["Digestion", "Growth", "Evaporation", "Reflection"], "B"),
            ("Photosynthesis mainly occurs in?", ["Roots", "Stem", "Leaves", "Flowers"], "C"),
            ("Which particle has a negative charge?", ["Proton", "Electron", "Neutron", "Photon"], "B"),
            ("Acids turn blue litmus to?", ["Green", "Red", "Yellow", "White"], "B"),
            ("Speed = ?", ["Distance / Time", "Time / Distance", "Mass / Volume", "Work / Time"], "A"),
            ("The ozone layer protects us from?", ["Rain", "UV rays", "Dust", "Wind"], "B"),
        ],
        "10-12": [
            ("Chemical symbol of sodium is?", ["So", "Sd", "Na", "S"], "C"),
            ("DNA stands for?", ["Deoxyribonucleic Acid", "Dynamic Neural Atom", "Double Nitric Acid", "Digital Nucleic Array"], "A"),
            ("pH value less than 7 means?", ["Neutral", "Basic", "Acidic", "Salty"], "C"),
            ("SI unit of force is?", ["Joule", "Newton", "Pascal", "Watt"], "B"),
            ("Mitochondria are called the?", ["Control center", "Powerhouse", "Protein factory", "Cell wall"], "B"),
            ("Velocity is a vector because it has?", ["Mass", "Direction", "Color", "Charge"], "B"),
            ("The study of heredity is?", ["Ecology", "Genetics", "Optics", "Astronomy"], "B"),
        ],
    },
    "general knowledge": {
        "1-3": [
            ("What is the capital of India?", ["Delhi", "Mumbai", "Chennai", "Kolkata"], "A"),
            ("How many days are there in a week?", ["5", "6", "7", "8"], "C"),
            ("Which festival is known as the festival of lights?", ["Holi", "Diwali", "Eid", "Christmas"], "B"),
            ("Which animal is called the king of the jungle?", ["Elephant", "Tiger", "Lion", "Bear"], "C"),
            ("How many colors are in a rainbow?", ["5", "6", "7", "8"], "C"),
            ("Which shape has four equal sides?", ["Circle", "Square", "Triangle", "Oval"], "B"),
            ("Which month comes after June?", ["May", "July", "August", "September"], "B"),
        ],
        "4-6": [
            ("Who wrote the national anthem of India?", ["Rabindranath Tagore", "Premchand", "Sarojini Naidu", "Bharatendu Harishchandra"], "A"),
            ("Which is the largest ocean?", ["Atlantic", "Indian", "Pacific", "Arctic"], "C"),
            ("How many states are there in India?", ["26", "28", "29", "30"], "B"),
            ("Which monument is in Agra?", ["Qutub Minar", "Taj Mahal", "Gateway of India", "Charminar"], "B"),
            ("Which is the fastest land animal?", ["Leopard", "Tiger", "Cheetah", "Horse"], "C"),
            ("Who is known as the Missile Man of India?", ["A.P.J. Abdul Kalam", "C.V. Raman", "Vikram Sarabhai", "Homi Bhabha"], "A"),
            ("What do we call a baby frog?", ["Larva", "Cub", "Tadpole", "Chick"], "C"),
        ],
        "7-9": [
            ("Which country gifted the Statue of Liberty to the USA?", ["France", "Germany", "Italy", "Spain"], "A"),
            ("Who painted the Mona Lisa?", ["Van Gogh", "Picasso", "Da Vinci", "Rembrandt"], "C"),
            ("Which is the smallest continent?", ["Europe", "Australia", "Antarctica", "South America"], "B"),
            ("What is the currency of Japan?", ["Won", "Yuan", "Yen", "Ringgit"], "C"),
            ("Which blood group is called universal donor?", ["A", "B", "AB", "O negative"], "D"),
            ("Who discovered gravity after seeing a falling apple?", ["Newton", "Galileo", "Edison", "Tesla"], "A"),
            ("Which desert is the largest hot desert?", ["Gobi", "Sahara", "Thar", "Kalahari"], "B"),
        ],
        "10-12": [
            ("Which article of the Indian Constitution deals with Right to Equality?", ["14", "19", "21", "32"], "A"),
            ("Who is the author of '1984'?", ["George Orwell", "Aldous Huxley", "Charles Dickens", "J.K. Rowling"], "A"),
            ("What is the headquarters of the UN?", ["Geneva", "Paris", "New York", "London"], "C"),
            ("Which planet has the most moons currently recognized in school-level GK?", ["Earth", "Mars", "Jupiter", "Mercury"], "C"),
            ("Who was the first woman Prime Minister of India?", ["Pratibha Patil", "Indira Gandhi", "Sarojini Naidu", "Sushma Swaraj"], "B"),
            ("World Environment Day is observed on?", ["June 5", "July 5", "April 22", "May 1"], "A"),
            ("Which Indian city is known as the Silicon Valley of India?", ["Hyderabad", "Bengaluru", "Pune", "Chennai"], "B"),
        ],
    },
}


def get_grade_band(class_level):
    digits = "".join(character for character in str(class_level) if character.isdigit())
    grade = int(digits or 1)
    if grade <= 3:
        return "1-3"
    if grade <= 6:
        return "4-6"
    if grade <= 9:
        return "7-9"
    return "10-12"


def generate_questions(subject, class_level):
    subject_key = subject.strip().lower()
    grade_band = get_grade_band(class_level)
    pool = QUESTION_BANK.get(subject_key, {}).get(grade_band, [])
    if len(pool) < 5:
        raise ValueError("Not enough questions available for the selected subject and grade.")
    return random.sample(pool, 5)


def get_parent_dashboard_data(parent_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, class_level, upi_id, wallet_balance
                FROM kids
                WHERE parent_id = %s
                ORDER BY created_at DESC
                """,
                (parent_id,),
            )
            kids = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    q.id,
                    q.subject,
                    q.reward_amount,
                    q.status,
                    q.launch_token,
                    q.created_at,
                    k.name AS kid_name,
                    k.class_level,
                    qa.score,
                    qa.passed,
                    rr.id AS reward_request_id,
                    rr.status AS reward_status
                FROM quizzes q
                JOIN kids k ON k.id = q.kid_id
                LEFT JOIN quiz_attempts qa ON qa.quiz_id = q.id
                LEFT JOIN reward_requests rr ON rr.quiz_id = q.id
                WHERE q.parent_id = %s
                ORDER BY q.created_at DESC
                """,
                (parent_id,),
            )
            quizzes = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    rr.id,
                    rr.requested_amount,
                    rr.status,
                    rr.requested_at,
                    k.name AS kid_name,
                    k.class_level,
                    q.subject
                FROM reward_requests rr
                JOIN kids k ON k.id = rr.kid_id
                JOIN quizzes q ON q.id = rr.quiz_id
                WHERE k.parent_id = %s
                ORDER BY rr.requested_at DESC
                """,
                (parent_id,),
            )
            reward_requests = cursor.fetchall()
    finally:
        connection.close()

    return {"kids": kids, "quizzes": quizzes, "reward_requests": reward_requests}


@app.route("/")
def index():
    if "parent_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.post("/login")
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, email FROM parents WHERE email = %s AND password = %s",
                (email, password),
            )
            parent = cursor.fetchone()
    finally:
        connection.close()

    if not parent:
        return render_template(
            "index.html",
            error="Invalid login. Try parent@kidvault.com / kidvault123 or your own parent account.",
        )

    session["parent_id"] = parent["id"]
    session["parent_email"] = parent["email"]
    return redirect(url_for("dashboard"))


@app.get("/dashboard")
@login_required
def dashboard():
    data = get_parent_dashboard_data(session["parent_id"])
    return render_template(
        "dashboard.html",
        parent_email=session.get("parent_email"),
        kids=data["kids"],
        quizzes=data["quizzes"],
        reward_requests=data["reward_requests"],
    )


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.post("/api/kids")
@login_required
def create_kid():
    payload = request.get_json(force=True)
    name = payload.get("name", "").strip()
    class_level = payload.get("class_level", "").strip()
    upi_id = payload.get("upi_id", "").strip() or None

    if not name or not class_level:
        return jsonify({"ok": False, "message": "Kid name and class are required."}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO kids (parent_id, name, class_level, upi_id)
                VALUES (%s, %s, %s, %s)
                """,
                (session["parent_id"], name, class_level, upi_id),
            )
        connection.commit()
    finally:
        connection.close()

    return jsonify({"ok": True, "message": "Kid profile saved."})


@app.post("/api/quizzes")
@login_required
def create_quiz():
    payload = request.get_json(force=True)
    kid_id = payload.get("kid_id")
    subject = payload.get("subject", "").strip().lower()
    reward_amount = payload.get("reward_amount")

    if not kid_id or not subject or reward_amount in (None, ""):
        return jsonify({"ok": False, "message": "Kid, subject, and reward are required."}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, class_level
                FROM kids
                WHERE id = %s AND parent_id = %s
                """,
                (kid_id, session["parent_id"]),
            )
            kid = cursor.fetchone()
            if not kid:
                return jsonify({"ok": False, "message": "Kid not found for this parent."}), 404

            questions = generate_questions(subject, kid["class_level"])
            launch_token = uuid.uuid4().hex[:12]

            cursor.execute(
                """
                INSERT INTO quizzes (parent_id, kid_id, subject, reward_amount, launch_token)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (session["parent_id"], kid_id, subject.title(), reward_amount, launch_token),
            )
            quiz_id = cursor.lastrowid

            for index, question in enumerate(questions, start=1):
                text, options, correct_option = question
                cursor.execute(
                    """
                    INSERT INTO quiz_questions (
                        quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, question_order
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (quiz_id, text, options[0], options[1], options[2], options[3], correct_option, index),
                )
        connection.commit()
    except ValueError as error:
        connection.rollback()
        return jsonify({"ok": False, "message": str(error)}), 400
    finally:
        connection.close()

    return jsonify(
        {
            "ok": True,
            "message": "Quiz launched successfully.",
            "launch_url": url_for("kid_quiz", token=launch_token),
            "launch_token": launch_token,
        }
    )


@app.get("/kid/<token>")
def kid_quiz(token):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    q.id,
                    q.subject,
                    q.reward_amount,
                    q.status,
                    k.name AS kid_name,
                    k.class_level,
                    k.wallet_balance
                FROM quizzes q
                JOIN kids k ON k.id = q.kid_id
                WHERE q.launch_token = %s
                """,
                (token,),
            )
            quiz = cursor.fetchone()
            if not quiz:
                return "Quiz not found.", 404

            cursor.execute(
                """
                SELECT id, question_text, option_a, option_b, option_c, option_d, question_order
                FROM quiz_questions
                WHERE quiz_id = %s
                ORDER BY question_order
                """,
                (quiz["id"],),
            )
            questions = cursor.fetchall()
    finally:
        connection.close()

    return render_template("kid_quiz.html", quiz=quiz, questions=questions, launch_token=token)


@app.post("/api/quiz/<token>/submit")
def submit_quiz(token):
    payload = request.get_json(force=True)
    answers = payload.get("answers", {})

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, kid_id, reward_amount, status
                FROM quizzes
                WHERE launch_token = %s
                """,
                (token,),
            )
            quiz = cursor.fetchone()
            if not quiz:
                return jsonify({"ok": False, "message": "Quiz not found."}), 404

            if quiz["status"] in {"completed", "reward_approved"}:
                return jsonify({"ok": False, "message": "This quiz has already been submitted."}), 400

            cursor.execute(
                """
                SELECT id, correct_option
                FROM quiz_questions
                WHERE quiz_id = %s
                """,
                (quiz["id"],),
            )
            questions = cursor.fetchall()

            score = 0
            for question in questions:
                if answers.get(str(question["id"])) == question["correct_option"]:
                    score += 1

            passed = int(score == len(questions))

            cursor.execute(
                """
                INSERT INTO quiz_attempts (quiz_id, score, passed)
                VALUES (%s, %s, %s)
                """,
                (quiz["id"], score, passed),
            )

            if passed:
                cursor.execute(
                    """
                    INSERT INTO reward_requests (quiz_id, kid_id, requested_amount, status)
                    VALUES (%s, %s, %s, 'pending')
                    """,
                    (quiz["id"], quiz["kid_id"], quiz["reward_amount"]),
                )
                new_status = "awaiting_parent_approval"
                message = "Perfect score! Reward request sent to the parent for approval."
            else:
                new_status = "completed"
                message = "Quiz completed. Reward unlocks only on all 5 correct answers."

            cursor.execute(
                "UPDATE quizzes SET status = %s WHERE id = %s",
                (new_status, quiz["id"]),
            )
        connection.commit()
    finally:
        connection.close()

    return jsonify({"ok": True, "score": score, "passed": bool(passed), "message": message})


@app.post("/api/reward/<int:request_id>/approve")
@login_required
def approve_reward(request_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    rr.id,
                    rr.kid_id,
                    rr.requested_amount,
                    rr.status,
                    rr.quiz_id,
                    k.parent_id
                FROM reward_requests rr
                JOIN kids k ON k.id = rr.kid_id
                WHERE rr.id = %s
                """,
                (request_id,),
            )
            reward = cursor.fetchone()
            if not reward or reward["parent_id"] != session["parent_id"]:
                return jsonify({"ok": False, "message": "Reward request not found."}), 404

            if reward["status"] == "approved":
                return jsonify({"ok": False, "message": "Reward already approved."}), 400

            cursor.execute(
                """
                UPDATE reward_requests
                SET status = 'approved', approved_at = %s
                WHERE id = %s
                """,
                (datetime.utcnow(), request_id),
            )
            cursor.execute(
                """
                UPDATE kids
                SET wallet_balance = wallet_balance + %s
                WHERE id = %s
                """,
                (reward["requested_amount"], reward["kid_id"]),
            )
            cursor.execute(
                """
                INSERT INTO wallet_transactions (kid_id, amount, type, note)
                VALUES (%s, %s, 'credit', 'Quiz reward approved by parent')
                """,
                (reward["kid_id"], reward["requested_amount"]),
            )
            cursor.execute(
                "UPDATE quizzes SET status = 'reward_approved' WHERE id = %s",
                (reward["quiz_id"],),
            )
        connection.commit()
    finally:
        connection.close()

    return jsonify({"ok": True, "message": "Reward approved and added to the kid wallet."})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
