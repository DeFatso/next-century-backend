from flask import request, jsonify
from werkzeug.security import check_password_hash
from db import get_db_connection
from . import teacher_bp

@teacher_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, full_name, email, password_hash 
            FROM users 
            WHERE role='teacher' AND email=%s
        """, (email,))
        teacher = cur.fetchone()
        conn.close()

        if not teacher:
            return jsonify({"error": "Invalid email"}), 401

        if not check_password_hash(teacher["password_hash"], password):
            return jsonify({"error": "Invalid password"}), 401

        return jsonify({
            "teacher_id": teacher["id"],
            "full_name": teacher["full_name"],
            "email": teacher["email"],
            "message": "Login successful"
        })
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500
