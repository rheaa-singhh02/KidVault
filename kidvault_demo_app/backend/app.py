import os
from datetime import datetime
from pathlib import Path

import pymysql
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory


load_dotenv()

app = Flask(__name__)
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", Path(__file__).resolve().parent.parent / "frontend"))
APP_INITIALIZED = False


QUESTION_BANK = {
    "Maths": {
        "text": "A pizza is cut into 8 slices. Rohan eats 3 slices. What fraction did he eat?",
        "options": ["1/4", "3/8", "5/8", "1/3"],
        "answer": "3/8",
    },
    "Science": {
        "text": "Which part of the plant makes food?",
        "options": ["Root", "Leaf", "Stem", "Flower"],
        "answer": "Leaf",
    },
    "GK": {
        "text": "What is the capital of India?",
        "options": ["Mumbai", "Delhi", "Chennai", "Kolkata"],
        "answer": "Delhi",
    },
}


def get_connection():
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
        CREATE TABLE IF NOT EXISTS demo_challenges (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject VARCHAR(50) NOT NULL,
            grade_label VARCHAR(50) NOT NULL,
            reward_amount INT NOT NULL,
            total_levels INT NOT NULL,
            completed_levels INT NOT NULL DEFAULT 0,
            status VARCHAR(30) NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS demo_quiz_attempts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            challenge_id INT NOT NULL,
            question_text TEXT NOT NULL,
            selected_answer VARCHAR(255),
            correct_answer VARCHAR(255) NOT NULL,
            is_correct TINYINT(1) NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (challenge_id) REFERENCES demo_challenges(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS demo_reward_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            challenge_id INT NOT NULL UNIQUE,
            amount INT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at DATETIME DEFAULT NULL,
            FOREIGN KEY (challenge_id) REFERENCES demo_challenges(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS demo_wallet (
            id INT PRIMARY KEY,
            balance INT NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """,
    ]

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
            cursor.execute("INSERT IGNORE INTO demo_wallet (id, balance) VALUES (1, 0)")
            cursor.execute("SELECT id FROM demo_challenges ORDER BY id DESC LIMIT 1")
            if not cursor.fetchone():
                cursor.execute(
                    """
                    INSERT INTO demo_challenges (
                        subject, grade_label, reward_amount, total_levels, completed_levels, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    ("Maths", "Class 5", 100, 3, 2, "active"),
                )
        connection.commit()
    finally:
        connection.close()


def ensure_initialized():
    global APP_INITIALIZED
    if APP_INITIALIZED:
        return
    init_db()
    APP_INITIALIZED = True


def get_current_challenge(cursor):
    cursor.execute(
        """
        SELECT *
        FROM demo_challenges
        ORDER BY id DESC
        LIMIT 1
        """
    )
    challenge = cursor.fetchone()
    if not challenge:
        raise RuntimeError("No demo challenge found.")
    return challenge


def build_state():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            challenge = get_current_challenge(cursor)

            cursor.execute(
                """
                SELECT id, amount, status, requested_at, approved_at
                FROM demo_reward_requests
                WHERE challenge_id = %s
                """,
                (challenge["id"],),
            )
            reward_request = cursor.fetchone()

            cursor.execute("SELECT balance FROM demo_wallet WHERE id = 1")
            wallet = cursor.fetchone()

            question = QUESTION_BANK.get(challenge["subject"], QUESTION_BANK["Maths"])

            request_status = "No reward request yet"
            approval_status = "Waiting for approval"
            reward_status = "Ready to send request" if challenge["completed_levels"] >= challenge["total_levels"] else "Complete the challenge first"

            if reward_request:
                request_status = f"Reward request {reward_request['status']}"
                approval_status = "Reward approved" if reward_request["status"] == "approved" else "Pending parent approval"
                reward_status = "Request approved" if reward_request["status"] == "approved" else "Request sent to parent"

            return {
                "challenge": {
                    "id": challenge["id"],
                    "subject": challenge["subject"],
                    "grade": challenge["grade_label"],
                    "reward": challenge["reward_amount"],
                    "levels": challenge["total_levels"],
                    "completed_levels": challenge["completed_levels"],
                    "status": challenge["status"],
                },
                "quiz": question,
                "reward_request": reward_request,
                "wallet_balance": wallet["balance"] if wallet else 0,
                "request_status": request_status,
                "approval_status": approval_status,
                "reward_status": reward_status,
            }
    finally:
        connection.close()


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@app.before_request
def initialize_before_request():
    ensure_initialized()


@app.get("/")
def home():
    return send_from_directory(FRONTEND_DIR, "demo-index.html")


@app.get("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


@app.get("/api/state")
def get_state():
    return jsonify({"ok": True, "state": build_state()})


@app.post("/api/challenge")
def save_challenge():
    payload = request.get_json(force=True)
    subject = payload.get("subject", "Maths")
    grade = payload.get("grade", "Class 5")
    reward = int(payload.get("reward", 100))
    levels = max(1, int(payload.get("levels", 3)))

    if subject not in QUESTION_BANK:
        return jsonify({"ok": False, "message": "Unsupported subject."}), 400

    completed_levels = max(levels - 1, 0)
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO demo_challenges (
                    subject, grade_label, reward_amount, total_levels, completed_levels, status
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (subject, grade, reward, levels, completed_levels, "active"),
            )
        connection.commit()
    finally:
        connection.close()

    return jsonify({"ok": True, "message": "Challenge saved.", "state": build_state()})


@app.post("/api/quiz/answer")
def submit_answer():
    payload = request.get_json(force=True)
    selected_answer = payload.get("selected_answer", "")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            challenge = get_current_challenge(cursor)
            question = QUESTION_BANK.get(challenge["subject"], QUESTION_BANK["Maths"])
            is_correct = int(selected_answer == question["answer"])

            cursor.execute(
                """
                INSERT INTO demo_quiz_attempts (
                    challenge_id, question_text, selected_answer, correct_answer, is_correct
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (challenge["id"], question["text"], selected_answer, question["answer"], is_correct),
            )

            if is_correct and challenge["completed_levels"] < challenge["total_levels"]:
                new_completed = challenge["completed_levels"] + 1
                new_status = "completed" if new_completed >= challenge["total_levels"] else "active"
                cursor.execute(
                    """
                    UPDATE demo_challenges
                    SET completed_levels = %s, status = %s
                    WHERE id = %s
                    """,
                    (new_completed, new_status, challenge["id"]),
                )
        connection.commit()
    finally:
        connection.close()

    message = "Correct answer. The final level is complete." if selected_answer == QUESTION_BANK.get(build_state()["challenge"]["subject"], QUESTION_BANK["Maths"])["answer"] else "That answer is not correct yet."
    return jsonify(
        {
            "ok": True,
            "correct": selected_answer == build_state()["quiz"]["answer"],
            "correct_answer": build_state()["quiz"]["answer"],
            "message": message,
            "state": build_state(),
        }
    )


@app.post("/api/reward/request")
def send_reward_request():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            challenge = get_current_challenge(cursor)
            if challenge["completed_levels"] < challenge["total_levels"]:
                return jsonify({"ok": False, "message": "Challenge is not complete yet."}), 400

            cursor.execute(
                "SELECT id, status FROM demo_reward_requests WHERE challenge_id = %s",
                (challenge["id"],),
            )
            existing = cursor.fetchone()
            if existing:
                return jsonify({"ok": False, "message": "Reward request already created."}), 400

            cursor.execute(
                """
                INSERT INTO demo_reward_requests (challenge_id, amount, status)
                VALUES (%s, %s, 'pending')
                """,
                (challenge["id"], challenge["reward_amount"]),
            )
            cursor.execute(
                "UPDATE demo_challenges SET status = 'reward_requested' WHERE id = %s",
                (challenge["id"],),
            )
        connection.commit()
    finally:
        connection.close()

    return jsonify({"ok": True, "message": "Reward request sent to parent.", "state": build_state()})


@app.post("/api/reward/approve")
def approve_reward():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            challenge = get_current_challenge(cursor)
            cursor.execute(
                "SELECT id, status FROM demo_reward_requests WHERE challenge_id = %s",
                (challenge["id"],),
            )
            reward_request = cursor.fetchone()
            if not reward_request:
                return jsonify({"ok": False, "message": "No reward request found."}), 404

            if reward_request["status"] == "approved":
                return jsonify({"ok": False, "message": "Reward already approved."}), 400

            cursor.execute(
                """
                UPDATE demo_reward_requests
                SET status = 'approved', approved_at = %s
                WHERE id = %s
                """,
                (datetime.utcnow(), reward_request["id"]),
            )
            cursor.execute(
                "UPDATE demo_wallet SET balance = balance + %s WHERE id = 1",
                (challenge["reward_amount"],),
            )
            cursor.execute(
                "UPDATE demo_challenges SET status = 'reward_approved' WHERE id = %s",
                (challenge["id"],),
            )
        connection.commit()
    finally:
        connection.close()

    return jsonify({"ok": True, "message": "Reward approved and added to wallet.", "state": build_state()})


@app.post("/api/reset")
def reset_demo():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute("TRUNCATE TABLE demo_reward_requests")
            cursor.execute("TRUNCATE TABLE demo_quiz_attempts")
            cursor.execute("TRUNCATE TABLE demo_challenges")
            cursor.execute("TRUNCATE TABLE demo_wallet")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            cursor.execute("INSERT INTO demo_wallet (id, balance) VALUES (1, 0)")
            cursor.execute(
                """
                INSERT INTO demo_challenges (
                    subject, grade_label, reward_amount, total_levels, completed_levels, status
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                ("Maths", "Class 5", 100, 3, 2, "active"),
            )
        connection.commit()
    finally:
        connection.close()

    return jsonify({"ok": True, "message": "Demo reset complete.", "state": build_state()})


if __name__ == "__main__":
    ensure_initialized()
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", os.getenv("FLASK_PORT", "5050"))),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
