# routes/subject_routes.py
from flask import Blueprint, jsonify
from db import get_db_connection
from flask_cors import cross_origin

# Create subject blueprint
subject_bp = Blueprint('subjects', __name__, url_prefix='/subjects')

# Get all subjects
@subject_bp.route('/', methods=['GET'])
@cross_origin()
def get_subjects():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT s.id, s.name, s.grade_id, g.name as grade_name
            FROM subjects s
            JOIN grades g ON s.grade_id = g.id
            ORDER BY g.name, s.name
        """)
        
        subjects = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(subjects)
        
    except Exception as e:
        return jsonify({
            "message": "Failed to fetch subjects",
            "error": "database_error",
            "details": str(e)
        }), 500

# Get subjects by grade
@subject_bp.route('/grade/<int:grade_id>', methods=['GET'])
@cross_origin()
def get_subjects_by_grade(grade_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT s.id, s.name, s.grade_id, g.name as grade_name
            FROM subjects s
            JOIN grades g ON s.grade_id = g.id
            WHERE s.grade_id = %s
            ORDER BY s.name
        """, (grade_id,))
        
        subjects = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(subjects)
        
    except Exception as e:
        return jsonify({
            "message": "Failed to fetch subjects",
            "error": "database_error",
            "details": str(e)
        }), 500