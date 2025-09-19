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
        
        # First get user info to determine role
        cur.execute("""
            SELECT id, full_name, email, role, grade_id, profile_pic_url, created_at, parent_id
            FROM users 
            WHERE id = %s
        """, (user_id,))
        user_info = cur.fetchone()
        
        if not user_info:
            return jsonify({"message": "User not found"}), 404

        display_name = user_info['full_name']
        grade_name = None
        child_id = None

        # If user is a parent, get their child's information
        if user_info['role'] == 'parent':
            # Get the first child (you might want to handle multiple children)
            cur.execute("""
                SELECT c.id, c.full_name, g.name as grade_name
                FROM users c
                LEFT JOIN grades g ON c.grade_id = g.id
                WHERE c.parent_id = %s
                LIMIT 1
            """, (user_id,))
            child_info = cur.fetchone()
            
            if child_info:
                display_name = child_info['full_name']  # Use child's name
                grade_name = child_info['grade_name']
                child_id = child_info['id']
            else:
                # Fallback: try to get from applications table
                cur.execute("""
                    SELECT child_name, g.name as grade_name
                    FROM applications a
                    JOIN grades g ON a.grade_id = g.id
                    WHERE a.parent_email = %s AND a.status = 'approved'
                    LIMIT 1
                """, (user_info['email'],))
                app_info = cur.fetchone()
                
                if app_info:
                    display_name = app_info['child_name']
                    grade_name = app_info['grade_name']
        
        # If user is a student, get their grade info
        else:
            if user_info['grade_id']:
                cur.execute("SELECT name FROM grades WHERE id = %s", (user_info['grade_id'],))
                grade_row = cur.fetchone()
                grade_name = grade_row['name'] if grade_row else None
            child_id = user_info['id']  # For students, use their own ID

        # Fetch upcoming assignments (use child_id for students, user_id for parents)
        assignment_user_id = child_id if child_id else user_id
        cur.execute("""
            SELECT a.id, a.title, a.due_date, s.name as subject_name
            FROM assignments a
            JOIN subjects s ON a.subject_id = s.id
            JOIN enrollments e ON s.grade_id = e.grade_id
            WHERE e.student_id = %s
            AND a.due_date BETWEEN NOW() AND NOW() + INTERVAL '7 days'
            ORDER BY a.due_date ASC
            LIMIT 5
        """, (assignment_user_id,))
        upcoming_assignments = cur.fetchall()

        # Fetch recent submissions
        cur.execute("""
            SELECT s.assignment_id, a.title, s.submitted_at, s.grade
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            WHERE s.student_id = %s
            ORDER BY s.submitted_at DESC
            LIMIT 5
        """, (assignment_user_id,))
        recent_submissions = cur.fetchall()

        cur.close()
        conn.close()

        return jsonify({
            "user": {
                "id": user_info['id'],
                "full_name": display_name,  # This will be child's name for parents
                "email": user_info['email'],
                "role": user_info['role'],
                "grade_name": grade_name,
                "profile_pic": user_info['profile_pic_url'],
                "member_since": user_info['created_at'].strftime('%B %Y')
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
        user_id = request.args.get('user_id')

        conn = get_db_connection()
        cur = conn.cursor()

        # Get user info
        cur.execute("""
            SELECT id, full_name, email, role, profile_pic_url, created_at, parent_id
            FROM users 
            WHERE id = %s
        """, (user_id,))
        user_info = cur.fetchone()

        if not user_info:
            return jsonify({"message": "User not found"}), 404

        display_name = user_info['full_name']
        grade_name = None

        # If user is a parent, get child info
        if user_info['role'] == 'parent':
            cur.execute("""
                SELECT c.full_name, g.name as grade_name
                FROM users c
                LEFT JOIN grades g ON c.grade_id = g.id
                WHERE c.parent_id = %s
                LIMIT 1
            """, (user_id,))
            child_info = cur.fetchone()
            
            if child_info:
                display_name = child_info['full_name']
                grade_name = child_info['grade_name']
            else:
                # Fallback to applications table
                cur.execute("""
                    SELECT child_name, g.name as grade_name
                    FROM applications a
                    JOIN grades g ON a.grade_id = g.id
                    WHERE a.parent_email = %s AND a.status = 'approved'
                    LIMIT 1
                """, (user_info['email'],))
                app_info = cur.fetchone()
                
                if app_info:
                    display_name = app_info['child_name']
                    grade_name = app_info['grade_name']
        
        # If user is a student, get their grade
        else:
            cur.execute("""
                SELECT g.name as grade_name
                FROM users u
                LEFT JOIN grades g ON u.grade_id = g.id
                WHERE u.id = %s
            """, (user_id,))
            grade_row = cur.fetchone()
            grade_name = grade_row['grade_name'] if grade_row else None

        cur.close()
        conn.close()

        return jsonify({
            "profile": {
                "id": user_info['id'],
                "full_name": display_name,  # Child's name for parents
                "email": user_info['email'],
                "role": user_info['role'],
                "grade_name": grade_name,
                "profile_picture": user_info['profile_pic_url'],
                "member_since": user_info['created_at'].strftime('%B %d, %Y'),
                "account_age_days": (datetime.datetime.now() - user_info['created_at']).days
            }
        })

    except Exception as e:
        return jsonify({"message": f"Error fetching profile: {str(e)}"}), 500