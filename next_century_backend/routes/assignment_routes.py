# routes/assignment_routes.py
from flask import Blueprint, jsonify, request
from db import get_db_connection
from flask_cors import cross_origin
from datetime import datetime, date
import math

assignment_bp = Blueprint('assignments', __name__, url_prefix='/assignments')

# Get upcoming assignments for a student
@assignment_bp.route('/student/<int:student_id>/upcoming', methods=['GET'])
@cross_origin()
def get_upcoming_assignments(student_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get student's grade first
        cur.execute("SELECT grade_id FROM users WHERE id = %s", (student_id,))
        student = cur.fetchone()
        
        if not student:
            return jsonify({"message": "Student not found", "error": "not_found"}), 404
        
        grade_id = student['grade_id']
        
        # Get upcoming assignments for the student's grade
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
        
        # Convert datetime objects to strings for JSON serialization
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

# Get recent activity for a student
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
        
        # Convert datetime objects to strings
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

# Get combined schedule data for dashboard
@assignment_bp.route('/student/<int:student_id>/schedule', methods=['GET'])
@cross_origin()
def get_student_schedule(student_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get upcoming assignments
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
        
        # Get recent activity
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
        
        # Convert datetime objects
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