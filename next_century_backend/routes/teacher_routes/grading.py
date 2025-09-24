from flask import request, jsonify
from db import get_db_connection
from . import teacher_bp

@teacher_bp.route("/grade", methods=["PUT"])
def grade_assignment():
    data = request.get_json()
    assignment_id = data.get("assignment_id")
    student_id = data.get("student_id")
    grade = data.get("grade")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE student_assignments
            SET grade=%s
            WHERE assignment_id=%s AND student_id=%s
        """, (grade, assignment_id, student_id))
        conn.commit()
        return jsonify({"message": "Assignment graded"})
    finally:
        cur.close()
        conn.close()
