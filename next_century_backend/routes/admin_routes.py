from flask import Blueprint, jsonify, request
from db import get_db_connection
from functools import wraps

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin credentials (should be in environment variables in production)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'supersecret'

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == ADMIN_USERNAME and auth.password == ADMIN_PASSWORD):
            return jsonify({
                "message": "Authentication required",
                "error": "invalid_credentials"
            }), 401
        return f(*args, **kwargs)
    return decorated

# Get all users for admin
@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                u.id, u.full_name, u.email, u.role, u.profile_pic_url,
                u.created_at, g.name as grade_name
            FROM users u
            LEFT JOIN grades g ON u.grade_id = g.id
            ORDER BY u.created_at DESC
        """)
        
        users = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(users)
        
    except Exception as e:
        return jsonify({
            "message": "Failed to fetch users",
            "error": "database_error",
            "details": str(e)
        }), 500

# Get admin dashboard statistics
@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_admin_stats():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Total users
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()['count']
        
        # Pending applications
        cur.execute("SELECT COUNT(*) FROM applications WHERE status = 'pending'")
        pending_apps = cur.fetchone()['count']
        
        # Total assignments
        cur.execute("SELECT COUNT(*) FROM assignments")
        total_assignments = cur.fetchone()['count']
        
        # Active students (users with role 'student')
        cur.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
        active_students = cur.fetchone()['count']
        
        # Total lessons
        cur.execute("SELECT COUNT(*) FROM lessons")
        total_lessons = cur.fetchone()['count']
        
        cur.close()
        conn.close()
        
        return jsonify({
            "total_users": total_users,
            "pending_applications": pending_apps,
            "total_assignments": total_assignments,
            "active_students": active_students,
            "total_lessons": total_lessons
        })
        
    except Exception as e:
        return jsonify({
            "message": "Failed to fetch statistics",
            "error": "database_error",
            "details": str(e)
        }), 500

# Delete user (admin only)
@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def admin_delete_user(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if user exists
        cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        
        if not user:
            return jsonify({
                "message": "User not found",
                "error": "not_found"
            }), 404
        
        # Delete user
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({
            "message": "User deleted successfully",
            "deleted_user_id": user_id
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "message": "Failed to delete user",
            "error": "database_error",
            "details": str(e)
        }), 500