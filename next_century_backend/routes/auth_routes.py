from flask import Blueprint, jsonify, request
from db import get_db_connection
import datetime


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

@auth_bp.route('/signup', methods=['POST'])
def signup():
    token = request.args.get('token')
    if not token:
        return jsonify({"message": "Missing signup token"}), 400

    data = request.get_json()
    password_hash = data.get('password_hash')

    if not password_hash:
        return jsonify({"message": "Password is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Validate token
    cur.execute("""
        SELECT application_id, expires_at FROM signup_tokens
        WHERE token = %s;
    """, (token,))
    token_row = cur.fetchone()

    if not token_row:
        cur.close()
        conn.close()
        return jsonify({"message": "Invalid or expired token"}), 400

    if token_row['expires_at'] < datetime.datetime.now():
        cur.close()
        conn.close()
        return jsonify({"message": "Token has expired"}), 400

    application_id = token_row['application_id']

    # Get application data
    cur.execute("""
        SELECT parent_name, parent_email, child_name, grade_id
        FROM applications
        WHERE id = %s;
    """, (application_id,))
    app_row = cur.fetchone()

    if not app_row:
        cur.close()
        conn.close()
        return jsonify({"message": "Associated application not found"}), 400

    # Create user
    cur.execute("""
        INSERT INTO users (full_name, email, password_hash, grade_id)
        VALUES (%s, %s, %s, %s) RETURNING id;
    """, (
        app_row['parent_name'],
        app_row['parent_email'],
        password_hash,
        app_row['grade_id']
    ))
    user_id = cur.fetchone()['id']

    # Clean up token
    cur.execute("DELETE FROM signup_tokens WHERE token=%s;", (token,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Signup complete", "user_id": user_id}), 201
