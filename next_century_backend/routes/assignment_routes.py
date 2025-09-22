# routes/assignment_routes.py
from flask import Blueprint, jsonify, request
from db import get_db_connection
from flask_cors import cross_origin
from datetime import datetime

assignment_bp = Blueprint('assignments', __name__, url_prefix='/assignments')

# ----------------------------
# Create a new assignment
# ----------------------------
@assignment_bp.route('', methods=['POST'])
@cross_origin()
def create_assignment():
    conn = None
    try:
        data = request.get_json()
        required_fields = ['title', 'subject_id', 'grade_id', 'due_date']
        
        if not all(field in data for field in required_fields):
            return jsonify({
                "message": "Missing required fields",
                "error": "missing_fields",
                "required": required_fields
            }), 400

        title = data['title']
        description = data.get('description', '')
        subject_id = data['subject_id']
        grade_id = data['grade_id']
        due_date = data['due_date']
        created_by = data.get('created_by')  # Optional: teacher ID

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO assignments (title, description, subject_id, grade_id, due_date, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, title, description, subject_id, grade_id, due_date, created_at
        """, (title, description, subject_id, grade_id, due_date, created_by))

        assignment = cur.fetchone()
        conn.commit()

        # Convert datetime to string
        if assignment['due_date']:
            assignment['due_date'] = assignment['due_date'].isoformat()
        if assignment['created_at']:
            assignment['created_at'] = assignment['created_at'].isoformat()

        cur.close()
        conn.close()

        return jsonify({
            "message": "Assignment created successfully",
            "assignment": assignment
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "message": "Failed to create assignment",
            "error": "database_error",
            "details": str(e)
        }), 500


# ----------------------------
# Update an assignment
# ----------------------------
@assignment_bp.route('/<int:assignment_id>', methods=['PUT'])
@cross_origin()
def update_assignment(assignment_id):
    conn = None
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if assignment exists
        cur.execute("SELECT id FROM assignments WHERE id = %s", (assignment_id,))
        if not cur.fetchone():
            return jsonify({"message": "Assignment not found"}), 404

        # Build update query dynamically
        update_fields = []
        update_values = []
        
        if 'title' in data:
            update_fields.append("title = %s")
            update_values.append(data['title'])
        if 'description' in data:
            update_fields.append("description = %s")
            update_values.append(data['description'])
        if 'subject_id' in data:
            update_fields.append("subject_id = %s")
            update_values.append(data['subject_id'])
        if 'due_date' in data:
            update_fields.append("due_date = %s")
            update_values.append(data['due_date'])
        
        if not update_fields:
            return jsonify({"message": "No fields to update"}), 400

        update_values.append(assignment_id)
        update_query = f"""
            UPDATE assignments 
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """

        cur.execute(update_query, update_values)
        assignment = cur.fetchone()
        conn.commit()

        if assignment['due_date']:
            assignment['due_date'] = assignment['due_date'].isoformat()

        cur.close()
        conn.close()

        return jsonify({
            "message": "Assignment updated successfully",
            "assignment": assignment
        })

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "message": "Failed to update assignment",
            "error": "database_error",
            "details": str(e)
        }), 500
        

# ----------------------------
# Submit assignment (student)
# ----------------------------
@assignment_bp.route('/<int:assignment_id>/submit', methods=['POST'])
@cross_origin()
def submit_assignment(assignment_id):
    conn = None
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({"message": "Student ID is required"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if already submitted
        cur.execute("""
            SELECT id FROM student_assignments 
            WHERE assignment_id = %s AND student_id = %s
        """, (assignment_id, student_id))
        
        if cur.fetchone():
            return jsonify({"message": "Assignment already submitted"}), 400

        # Insert submission
        cur.execute("""
            INSERT INTO student_assignments (assignment_id, student_id, status, submitted_at)
            VALUES (%s, %s, 'submitted', NOW())
            RETURNING *
        """, (assignment_id, student_id))

        submission = cur.fetchone()
        conn.commit()

        if submission['submitted_at']:
            submission['submitted_at'] = submission['submitted_at'].isoformat()

        cur.close()
        conn.close()

        return jsonify({
            "message": "Assignment submitted successfully",
            "submission": submission
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "message": "Failed to submit assignment",
            "error": "database_error",
            "details": str(e)
        }), 500


# ----------------------------
# Grade assignment (teacher)
# ----------------------------
@assignment_bp.route('/<int:assignment_id>/grade', methods=['POST'])
@cross_origin()
def grade_assignment(assignment_id):
    conn = None
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        grade = data.get('grade')
        feedback = data.get('feedback', '')
        
        if not student_id or grade is None:
            return jsonify({"message": "Student ID and grade are required"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE student_assignments 
            SET grade = %s, feedback = %s, status = 'graded'
            WHERE assignment_id = %s AND student_id = %s
            RETURNING *
        """, (grade, feedback, assignment_id, student_id))

        if cur.rowcount == 0:
            return jsonify({"message": "Submission not found"}), 404

        graded_assignment = cur.fetchone()
        conn.commit()

        if 'submitted_at' in graded_assignment and graded_assignment['submitted_at']:
            graded_assignment['submitted_at'] = graded_assignment['submitted_at'].isoformat()

        cur.close()
        conn.close()

        return jsonify({
            "message": "Assignment graded successfully",
            "submission": graded_assignment
        })

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "message": "Failed to grade assignment",
            "error": "database_error",
            "details": str(e)
        }), 500


# ----------------------------
# Get upcoming assignments for a student
# ----------------------------
@assignment_bp.route('/student/<int:student_id>/upcoming', methods=['GET'])
@cross_origin()
def get_upcoming_assignments(student_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT grade_id FROM users WHERE id = %s", (student_id,))
        student = cur.fetchone()
        
        if not student:
            return jsonify({"message": "Student not found", "error": "not_found"}), 404
        
        grade_id = student['grade_id']
        
        cur.execute("""
            SELECT 
                a.id, 
                a.title, 
                a.due_date,
                s.name as subject_name,
                (a.due_date - CURRENT_DATE) as days_until_due
            FROM assignments a
            JOIN subjects s ON a.subject_id = s.id
            WHERE a.grade_id = %s 
            AND a.due_date >= CURRENT_DATE
            ORDER BY a.due_date ASC
            LIMIT 10
        """, (grade_id,))
        
        assignments = cur.fetchall()
        
        for assignment in assignments:
            if assignment['due_date']:
                assignment['due_date'] = assignment['due_date'].isoformat()
        
        cur.close()
        conn.close()
        
        return jsonify(assignments)
        
    except Exception as e:
        return jsonify({
            "message": "Failed to fetch upcoming assignments",
            "error": "database_error",
            "details": str(e)
        }), 500


# ----------------------------
# Get recent activity for a student
# ----------------------------
@assignment_bp.route('/student/<int:student_id>/recent-activity', methods=['GET'])
@cross_origin()
def get_recent_activity(student_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                sa.assignment_id,
                a.title,
                sa.submitted_at,
                sa.grade,
                sa.status,
                s.name as subject_name
            FROM student_assignments sa
            JOIN assignments a ON sa.assignment_id = a.id
            JOIN subjects s ON a.subject_id = s.id
            WHERE sa.student_id = %s
            ORDER BY sa.submitted_at DESC
            LIMIT 10
        """, (student_id,))
        
        activities = cur.fetchall()
        
        for activity in activities:
            if activity['submitted_at']:
                activity['submitted_at'] = activity['submitted_at'].isoformat()
        
        cur.close()
        conn.close()
        
        return jsonify(activities)
        
    except Exception as e:
        return jsonify({
            "message": "Failed to fetch recent activity",
            "error": "database_error",
            "details": str(e)
        }), 500


# ----------------------------
# Get combined schedule data for dashboard
# ----------------------------
@assignment_bp.route('/student/<int:student_id>/schedule', methods=['GET'])
@cross_origin()
def get_student_schedule(student_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                a.id, 
                a.title, 
                a.due_date,
                s.name as subject,
                (a.due_date - CURRENT_DATE) as days_until_due
            FROM assignments a
            JOIN subjects s ON a.subject_id = s.id
            JOIN users u ON a.grade_id = u.grade_id
            WHERE u.id = %s 
            AND a.due_date >= CURRENT_DATE
            ORDER BY a.due_date ASC
            LIMIT 5
        """, (student_id,))
        
        upcoming_assignments = cur.fetchall()
        
        cur.execute("""
            SELECT 
                sa.assignment_id,
                a.title,
                sa.submitted_at,
                sa.grade,
                s.name as subject
            FROM student_assignments sa
            JOIN assignments a ON sa.assignment_id = a.id
            JOIN subjects s ON a.subject_id = s.id
            WHERE sa.student_id = %s
            ORDER BY sa.submitted_at DESC
            LIMIT 5
        """, (student_id,))
        
        recent_activity = cur.fetchall()
        
        for assignment in upcoming_assignments:
            if assignment['due_date']:
                assignment['due_date'] = assignment['due_date'].strftime('%Y-%m-%d')
        
        for activity in recent_activity:
            if activity['submitted_at']:
                activity['submitted_at'] = activity['submitted_at'].strftime('%Y-%m-%d %H:%M')
        
        cur.close()
        conn.close()
        
        return jsonify({
            "upcoming_assignments": upcoming_assignments,
            "recent_activity": recent_activity
        })
        
    except Exception as e:
        return jsonify({
            "message": "Failed to fetch schedule data",
            "error": "database_error",
            "details": str(e)
        }), 500
