from flask import Blueprint, jsonify, request
from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from functools import wraps

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# CORS headers helper function
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Authentication logic to be added later
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        response = jsonify({})
        return add_cors_headers(response)

    data = request.get_json()
    required_fields = ['full_name', 'email', 'password', 'grade_id']
    
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400

    full_name = data['full_name']
    email = data['email']
    password = data['password']
    grade_id = data['grade_id']
    role = data.get('role', 'student')

    # Hash the password
    password_hash = generate_password_hash(password)

    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO users (full_name, email, password_hash, grade_id, role)
            VALUES (%s, %s, %s, %s, %s) RETURNING id;
        """, (full_name, email, password_hash, grade_id, role))
        
        user_id = cur.fetchone()['id']
        conn.commit()
        
        return jsonify({
            "id": user_id, 
            "message": "User registered successfully"
        }), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Registration failed: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()

@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        response = jsonify({})
        return add_cors_headers(response)

    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"message": "Email and password are required"}), 400

    email = data['email']
    password = data['password']

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get user with role information
        cur.execute("""
            SELECT id, full_name, email, grade_id, password_hash, role, parent_id
            FROM users
            WHERE email = %s;
        """, (email,))
        user = cur.fetchone()

        if not user:
            return jsonify({"message": "User not found"}), 404

        # Compare the provided password with the stored hash
        if not check_password_hash(user['password_hash'], password):
            return jsonify({"message": "Invalid password"}), 401

        # Login successful
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user['id'],
                "full_name": user['full_name'],
                "email": user['email'],
                "grade_id": user['grade_id'],
                "role": user['role'],
                "parent_id": user['parent_id']
            }
        })
    except Exception as e:
        return jsonify({"message": f"Server error: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()

@auth_bp.route('/signup', methods=['POST', 'OPTIONS'])
def signup():
    if request.method == 'OPTIONS':
        response = jsonify({})
        return add_cors_headers(response)

    data = request.get_json()
    token = data.get("token")
    password = data.get("password")

    if not token or not password:
        return jsonify({"message": "Missing token or password"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Validate token
        cur.execute("""
            SELECT application_id, expires_at FROM signup_tokens
            WHERE token = %s
        """, (token,))
        token_row = cur.fetchone()

        if not token_row:
            return jsonify({"message": "Invalid or expired token"}), 400

        if token_row["expires_at"] < datetime.datetime.now():
            return jsonify({"message": "Token has expired"}), 400

        application_id = token_row["application_id"]

        # Get application data including child_name
        cur.execute("""
            SELECT parent_name, parent_email, child_name, grade_id
            FROM applications
            WHERE id = %s
        """, (application_id,))
        app_row = cur.fetchone()

        if not app_row:
            return jsonify({"message": "Associated application not found"}), 400

        # Hash password
        password_hash = generate_password_hash(password)

        # Create parent account
        cur.execute("""
            INSERT INTO users (full_name, email, password_hash, role, created_at)
            VALUES (%s, %s, %s, 'parent', NOW())
            RETURNING id
        """, (
            app_row["parent_name"],
            app_row["parent_email"],
            password_hash
        ))
        parent_id = cur.fetchone()["id"]

        # Create child account linked to parent (grade_id is set directly - no enrollments needed)
        cur.execute("""
            INSERT INTO users (full_name, email, password_hash, role, parent_id, grade_id, created_at)
            VALUES (%s, %s, %s, 'student', %s, %s, NOW())
            RETURNING id
        """, (
            app_row["child_name"],
            f"child_{app_row['parent_email']}",  # Generate unique email for child
            password_hash,
            parent_id,
            app_row["grade_id"]  # Grade is set directly - no enrollments table needed
        ))
        child_id = cur.fetchone()["id"]

        # Delete token
        cur.execute("DELETE FROM signup_tokens WHERE token = %s", (token,))
        
        conn.commit()

        return jsonify({
            "message": "Signup complete",
            "parent_id": parent_id,
            "child_id": child_id
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Signup failed: {str(e)}"}), 500
    finally:
        cur.close()
        conn.close()

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"message": "User ID is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get user info
        cur.execute("""
            SELECT id, full_name, email, role, profile_pic_url, created_at, parent_id, grade_id
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

        return jsonify({
            "profile": {
                "id": user_info['id'],
                "full_name": display_name,
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
    finally:
        cur.close()
        conn.close()

# Optional: Add a health check endpoint
@auth_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "auth"})