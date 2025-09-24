from flask import Blueprint, request, jsonify
from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')


# ---------------------------
# POST: Teacher Login
# ---------------------------
@teacher_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, full_name, email, password_hash
            FROM users
            WHERE role = 'teacher' AND email = %s
        """, (email,))
        teacher = cur.fetchone()
        conn.close()

        if teacher is None:
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


# ---------------------------
# GET: Teacher Dashboard
# ---------------------------
@teacher_bp.route('/dashboard/<int:teacher_id>', methods=['GET'])
def dashboard(teacher_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch lessons created by this teacher
    cur.execute("""
        SELECT id, title, description, grade_id, zoom_link, youtube_link
        FROM lessons
        WHERE created_by = %s
        ORDER BY id
    """, (teacher_id,))
    lessons = cur.fetchall()

    lesson_list = []
    for l in lessons:
        lesson_list.append({
            "id": l["id"],
            "title": l["title"],
            "description": l["description"],
            "grade_id": l["grade_id"],
            "zoom_link": l["zoom_link"],
            "youtube_link": l["youtube_link"]
        })

    conn.close()
    return jsonify({
        "teacher_id": teacher_id,
        "lessons": lesson_list
    })


# ---------------------------
# POST: Add a Lesson
# ---------------------------
@teacher_bp.route("/lessons", methods=["POST"])
def add_lesson():
    data = request.get_json()
    
    # Debug: Print received data
    print("Received lesson data:", data)

    teacher_id = data.get("teacher_id")
    title = data.get("title")
    description = data.get("description")
    grade_id = data.get("grade_id")
    zoom_link = data.get("zoom_link", "")
    youtube_link = data.get("youtube_link", "")

    if not all([teacher_id, title, description, grade_id]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check if teacher exists
        cur.execute("SELECT id FROM users WHERE id = %s AND role = 'teacher'", (teacher_id,))
        teacher = cur.fetchone()
        if not teacher:
            return jsonify({"error": "Teacher not found"}), 404

        # Check if grade exists
        cur.execute("SELECT id FROM grades WHERE id = %s", (grade_id,))
        grade = cur.fetchone()
        if not grade:
            return jsonify({"error": "Grade not found"}), 404

        # INSERT the lesson
        cur.execute("""
            INSERT INTO lessons (created_by, title, description, grade_id, zoom_link, youtube_link, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            teacher_id,
            title,
            description,
            grade_id,
            zoom_link,
            youtube_link,
            datetime.utcnow(),
            datetime.utcnow()
        ))

        lesson_id_row = cur.fetchone()
        if lesson_id_row is None:
            raise Exception("Failed to insert lesson")

        lesson_id = lesson_id_row["id"]  # Use dictionary access, not index
        conn.commit()
        
        return jsonify({
            "message": "Lesson created successfully",
            "lesson_id": lesson_id
        }), 201

    except Exception as e:
        conn.rollback()
        # Provide more detailed error information
        import traceback
        error_details = traceback.format_exc()
        print("Error details:", error_details)
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    finally:
        cur.close()
        conn.close()

# ---------------------------
# PUT: Edit a Lesson
# ---------------------------
@teacher_bp.route('/lessons/<int:lesson_id>', methods=['PUT'])
def edit_lesson(lesson_id):
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    grade_id = data.get('grade_id')
    zoom_link = data.get('zoom_link')
    youtube_link = data.get('youtube_link')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE lessons
        SET title = %s, description = %s, grade_id = %s, zoom_link = %s, youtube_link = %s, updated_at = %s
        WHERE id = %s
    """, (title, description, grade_id, zoom_link, youtube_link, datetime.utcnow(), lesson_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Lesson updated"})


# ---------------------------
# DELETE: Remove a Lesson
# ---------------------------
@teacher_bp.route('/lessons/<int:lesson_id>', methods=['DELETE'])
def delete_lesson(lesson_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM lessons WHERE id = %s", (lesson_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Lesson deleted"})


# ---------------------------
# PUT: Grade a Student Assignment
# ---------------------------
@teacher_bp.route('/grade', methods=['PUT'])
def grade_assignment():
    data = request.get_json()
    assignment_id = data.get('assignment_id')
    student_id = data.get('student_id')
    grade = data.get('grade')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE student_assignments
        SET grade = %s
        WHERE assignment_id = %s AND student_id = %s
    """, (grade, assignment_id, student_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Assignment graded"})
