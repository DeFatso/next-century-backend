# routes/grade_routes.py
from flask import Blueprint, jsonify
from db import get_db_connection
from flask_cors import cross_origin
from routes.lesson_routes import lesson_bp

grade_bp = Blueprint('grades', __name__, url_prefix='/grades')

@grade_bp.route('/', methods=['GET'])
@cross_origin()
def get_grades():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM grades ORDER BY name")
        grades = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(grades)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# routes/lesson_routes.py - Add grade-based lesson fetching
@lesson_bp.route('/grade/<int:grade_id>', methods=['GET'])
@cross_origin()
def get_lessons_by_grade(grade_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT l.*, s.name as subject_name
            FROM lessons l
            JOIN subjects s ON l.subject_id = s.id
            WHERE s.grade_id = %s
            ORDER BY l.created_at DESC
        """, (grade_id,))
        lessons = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(lessons)
    except Exception as e:
        return jsonify({"error": str(e)}), 500