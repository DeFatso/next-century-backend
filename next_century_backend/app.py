from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)

# DB connection info
DB_HOST = "localhost"
DB_NAME = "next_century"
DB_USER = "school_admin"
DB_PASS = input("Enter your database password: ")

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        cursor_factory=RealDictCursor
    )
    return conn


@app.route('/')
def home():
    return jsonify({"message": "Welcome to Next Century Online School API!"})


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    full_name = data['full_name']
    email = data['email']
    password_hash = data['password_hash']  # In production, hash properly!
    role = data['role']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (full_name, email, password_hash, role)
        VALUES (%s, %s, %s, %s) RETURNING id;
    """, (full_name, email, password_hash, role))
    user_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"id": user_id, "message": "User registered"}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password_hash = data['password_hash']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, role FROM users WHERE email=%s AND password_hash=%s;
    """, (email, password_hash))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        return jsonify({"id": user['id'], "role": user['role'], "message": "Login successful"})
    else:
        return jsonify({"message": "Invalid credentials"}), 401


@app.route('/grades')
def get_grades():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, name FROM grades;')
    grades = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(grades)


@app.route('/subjects/<int:grade_id>')
def get_subjects(grade_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name FROM subjects WHERE grade_id=%s;
    """, (grade_id,))
    subjects = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(subjects)


@app.route('/lessons/<int:subject_id>')
def get_lessons(subject_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, content_text, video_url
        FROM lessons WHERE subject_id=%s;
    """, (subject_id,))
    lessons = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(lessons)


@app.route('/assignments', methods=['POST'])
def create_assignment():
    data = request.get_json()
    subject_id = data['subject_id']
    title = data['title']
    description = data.get('description')
    due_date = data.get('due_date')
    created_by = data['created_by']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO assignments (subject_id, title, description, due_date, created_by)
        VALUES (%s, %s, %s, %s, %s) RETURNING id;
    """, (subject_id, title, description, due_date, created_by))
    assignment_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"id": assignment_id, "message": "Assignment created"}), 201


@app.route('/submissions', methods=['POST'])
def submit_assignment():
    data = request.get_json()
    assignment_id = data['assignment_id']
    student_id = data['student_id']
    file_url = data['file_url']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO submissions (assignment_id, student_id, file_url)
        VALUES (%s, %s, %s) RETURNING id;
    """, (assignment_id, student_id, file_url))
    submission_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"id": submission_id, "message": "Submission successful"}), 201


if __name__ == '__main__':
    app.run(debug=True)
