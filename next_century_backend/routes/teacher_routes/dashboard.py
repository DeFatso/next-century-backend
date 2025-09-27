from flask import Blueprint, jsonify
from db import get_db_connection
from datetime import datetime

teacher_dashboard_bp = Blueprint("teacher_dashboard", __name__)

DEFAULT_PROFILE_PIC = "https://example.com/default-profile.png"

@teacher_dashboard_bp.route("/", methods=["GET"])
def teacher_dashboard_home():
    return jsonify({"message": "Teacher Dashboard active"})


@teacher_dashboard_bp.route("/profile/<int:teacher_id>", methods=["GET"])
def teacher_profile(teacher_id):
    """
    Fetch teacher profile by ID, including lessons and assignments.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch teacher info
    cur.execute(
        "SELECT id, full_name, email, profile_pic_url FROM users WHERE id = %s AND role = 'teacher'",
        (teacher_id,)
    )
    teacher_row = cur.fetchone()
    if not teacher_row:
        cur.close()
        conn.close()
        return jsonify({"error": "Teacher not found"}), 404

    # Convert to dictionary
    teacher = {
        "id": teacher_row["id"],
        "full_name": teacher_row["full_name"],
        "email": teacher_row["email"],
        "profile_pic_url": teacher_row["profile_pic_url"] or DEFAULT_PROFILE_PIC
    }

    # Fetch lessons
    cur.execute(
        "SELECT id, title, description FROM lessons WHERE created_by = %s ORDER BY id DESC",
        (teacher_id,)
    )
    lessons = [{"id": row["id"], "title": row["title"], "description": row["description"]} for row in cur.fetchall()]

    # Fetch assignments
    cur.execute(
        """
        SELECT id, title, description, due_date 
        FROM assignments 
        WHERE created_by = %s 
        ORDER BY due_date ASC
        """,
        (teacher_id,)
    )
    assignments = [
        {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "due_date": row["due_date"].strftime("%Y-%m-%d") if row["due_date"] else None
        }
        for row in cur.fetchall()
    ]

    cur.close()
    conn.close()

    # Combine all data
    teacher["lessons"] = lessons
    teacher["assignments"] = assignments

    return jsonify({"teacher": teacher})
