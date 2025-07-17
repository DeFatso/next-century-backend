from flask import Blueprint, jsonify, request
from db import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    full_name = data['full_name']
    email = data['email']
    password_hash = data['password_hash']
    grade_id = data['grade_id']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (full_name, email, password_hash, grade_id)
        VALUES (%s, %s, %s, %s) RETURNING id;
    """, (full_name, email, password_hash, grade_id))
    user_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"id": user_id, "message": "User registered"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password_hash = data['password_hash']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, full_name, email, grade_id
        FROM users
        WHERE email=%s AND password_hash=%s;
    """, (email, password_hash))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user['id'],
                "full_name": user['full_name'],
                "email": user['email'],
                "grade_id": user['grade_id']
            }
        })
    else:
        return jsonify({"message": "Invalid credentials"}), 401
