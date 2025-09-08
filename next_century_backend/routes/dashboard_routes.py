from flask import Blueprint, jsonify, request
from db import get_db_connection
from functools import wraps
import datetime
from routes.auth_routes import auth_bp

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# Decorator to protect routes (placeholder)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Authentication logic to be added later
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/dashboard', methods=['GET'])
@login_required
def user_dashboard():
    try:
        user_id = request.args.get('user_id')  # Temporary auth
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Fetch user info along with grade in a single query
        cur.execute("""
            SELECT u.id, u.full_name, u.email, u.role, u.grade_id, u.profile_pic_url,
                   u.created_at, g.name as grade_name
            FROM users u
            LEFT JOIN grades g ON u.grade_id = g.id
            WHERE u.id = %s
        """, (user_id,))
        user = cur.fetchone()
        
        if not user:
            return jsonify({"message": "User not found"}), 404

        # Fetch upcoming assignments (next 7 days)
        cur.execute("""
            SELECT a.id, a.title, a.due_date, s.name as subject_name
            FROM assignments a
            JOIN subjects s ON a.subject_id = s.id
            JOIN enrollments e ON s.grade_id = e.grade_id
            WHERE e.student_id = %s
            AND a.due_date BETWEEN NOW() AND NOW() + INTERVAL '7 days'
            ORDER BY a.due_date ASC
            LIMIT 5
        """, (user_id,))
        upcoming_assignments = cur.fetchall()
        
        # Fetch recent submissions
        cur.execute("""
            SELECT s.assignment_id, a.title, s.submitted_at, s.grade
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            WHERE s.student_id = %s
            ORDER BY s.submitted_at DESC
            LIMIT 5
        """, (user_id,))
        recent_submissions = cur.fetchall()
        
        cur.close()
        conn.close()

        return jsonify({
            "user": {
                "id": user['id'],
                "full_name": user['full_name'],
                "email": user['email'],
                "role": user['role'],
                "grade_name": user['grade_name'],
                "profile_pic": user['profile_pic_url'],
                "member_since": user['created_at'].strftime('%B %Y')
            },
            "upcoming_assignments": [
                {
                    "id": assignment['id'],
                    "title": assignment['title'],
                    "due_date": assignment['due_date'].strftime('%Y-%m-%d'),
                    "subject": assignment['subject_name'],
                    "days_until_due": (assignment['due_date'] - datetime.datetime.now()).days
                } for assignment in upcoming_assignments
            ],
            "recent_activity": [
                {
                    "assignment_id": sub['assignment_id'],
                    "title": sub['title'],
                    "submitted_at": sub['submitted_at'].strftime('%Y-%m-%d %H:%M'),
                    "grade": sub['grade']
                } for sub in recent_submissions
            ]
        })
        
    except Exception as e:
        return jsonify({"message": f"Error fetching dashboard: {str(e)}"}), 500


@auth_bp.route('/profile', methods=['GET'])
@login_required
def user_profile():
    try:
        user_id = request.args.get('user_id')  # Temporary auth
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT u.id, u.full_name, u.email, u.role, u.profile_pic_url, 
                   u.created_at, g.name as grade_name
            FROM users u
            LEFT JOIN grades g ON u.grade_id = g.id
            WHERE u.id = %s
        """, (user_id,))
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user:
            return jsonify({"message": "User not found"}), 404

        return jsonify({
            "profile": {
                "id": user['id'],
                "full_name": user['full_name'],
                "email": user['email'],
                "role": user['role'],
                "grade_name": user['grade_name'],
                "profile_picture": user['profile_pic_url'],
                "member_since": user['created_at'].strftime('%B %d, %Y'),
                "account_age_days": (datetime.datetime.now() - user['created_at']).days
            }
        })
            
    except Exception as e:
        return jsonify({"message": f"Error fetching profile: {str(e)}"}), 500
