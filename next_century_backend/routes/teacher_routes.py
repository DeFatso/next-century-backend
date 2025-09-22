from flask import Blueprint, request, jsonify
from db import get_db_connection
from werkzeug.security import generate_password_hash

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')


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

    # If using DictCursor
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
@teacher_bp.route('/lessons', methods=['POST'])
def add_lesson():
    data = request.get_json()
    teacher_id = data.get('teacher_id')
    title = data.get('title')
    description = data.get('description')
    grade_id = data.get('grade_id')
    zoom_link = data.get('zoom_link')
    youtube_link = data.get('youtube_link')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO lessons (title, description, grade_id, created_by, zoom_link, youtube_link)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
    """, (title, description, grade_id, teacher_id, zoom_link, youtube_link))
    lesson_id = cur.fetchone()[0]
    conn.commit()
    conn.close()

    return jsonify({"message": "Lesson created", "lesson_id": lesson_id})


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
        SET title = %s, description = %s, grade_id = %s, zoom_link = %s, youtube_link = %s
        WHERE id = %s
    """, (title, description, grade_id, zoom_link, youtube_link, lesson_id))
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
