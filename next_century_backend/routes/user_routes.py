from flask import Blueprint, jsonify, request
from db import get_db_connection

# 🚨 Removed `strict_slashes=False` here
user_bp = Blueprint('users', __name__)

@user_bp.route('/', methods=['GET'])
def list_users():
    conn = get_db_connection()
    cur = conn.cursor()
    # Join with grades to get grade_name
    cur.execute("""
        SELECT u.id, u.full_name, u.email, u.grade_id, g.name AS grade_name,
               u.profile_pic_url, u.created_at
        FROM users u
        LEFT JOIN grades g ON u.grade_id = g.id;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Convert rows to dict
    users = []
    for user in rows:
        users.append({
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "grade_id": user["grade_id"],
            "grade_name": user["grade_name"],
            "profile_pic_url": user["profile_pic_url"],
            "created_at": user["created_at"].isoformat()  # optional: ISO format
        })

    return jsonify(users)


@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id, u.full_name, u.email, u.grade_id, g.name AS grade_name,
               u.profile_pic_url, u.created_at
        FROM users u
        LEFT JOIN grades g ON u.grade_id = g.id
        WHERE u.id = %s;
    """, (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        # Access columns by name, not index
        user_dict = {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "grade_id": user["grade_id"],
            "grade_name": user["grade_name"],
            "profile_pic_url": user["profile_pic_url"],
            "created_at": user["created_at"]
        }
        return jsonify(user_dict)
    else:
        return jsonify({"message": "User not found"}), 404



@user_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    full_name = data.get('full_name')
    email = data.get('email')
    grade_id = data.get('grade_id')
    profile_pic_url = data.get('profile_pic_url')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users
        SET full_name=%s, email=%s, grade_id=%s, profile_pic_url=%s
        WHERE id=%s
        RETURNING id;
    """, (full_name, email, grade_id, profile_pic_url, user_id))
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if updated:
        return jsonify({"id": updated['id'], "message": "User updated"})
    else:
        return jsonify({"message": "User not found"}), 404

@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=%s RETURNING id;", (user_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if deleted:
        return jsonify({"id": deleted['id'], "message": "User deleted"})
    else:
        return jsonify({"message": "User not found"}), 404

