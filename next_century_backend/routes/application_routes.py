import psycopg2
import psycopg2.extras

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="next_century_db",
        user="postgres",
        password="clarity"
    )
    # Use DictCursor for dictionary results
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn

from flask import Blueprint, jsonify, request
from db import get_db_connection
from mailer import send_signup_email
from functools import wraps
import uuid
import datetime
from flask_cors import cross_origin

application_bp = Blueprint('applications', __name__, url_prefix='/applications')

# Admin credentials (should be in environment variables in production)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'supersecret'

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Handle OPTIONS requests for CORS preflight
        if request.method == 'OPTIONS':
            return jsonify({}), 200

        auth = request.authorization
        if not auth or not (auth.username == ADMIN_USERNAME and auth.password == ADMIN_PASSWORD):
            return jsonify({
                "message": "Authentication required",
                "error": "invalid_credentials"
            }), 401
        return f(*args, **kwargs)
    return decorated

# 📄 Public — submit application
@application_bp.route('/apply', methods=['POST', 'OPTIONS'])
@cross_origin()
def apply():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    if not request.is_json:
        return jsonify({
            "message": "Request must be JSON",
            "error": "invalid_content_type"
        }), 400

    data = request.get_json()
    required_fields = {
        "parentName": "Parent name",
        "email": "Email",
        "childName": "Child name",
        "grade": "Grade"
    }

    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return jsonify({
            "message": "Missing required fields",
            "missing": [required_fields[field] for field in missing_fields],
            "error": "missing_fields"
        }), 400

    parent_name = data["parentName"]
    parent_email = data["email"]
    child_name = data["childName"]
    grade_name = data["grade"]

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get grade id
        cur.execute("SELECT id FROM grades WHERE name = %s", (grade_name,))
        grade_row = cur.fetchone()
        if not grade_row:
            return jsonify({
                "message": "Invalid grade selected",
                "error": "invalid_grade"
            }), 400

        grade_id = grade_row["id"]

        # Insert application
        cur.execute("""
            INSERT INTO applications (parent_name, parent_email, child_name, grade_id, status, created_at)
            VALUES (%s, %s, %s, %s, 'pending', NOW())
            RETURNING id
        """, (parent_name, parent_email, child_name, grade_id))

        application_id = cur.fetchone()["id"]
        conn.commit()

        return jsonify({
            "message": "Application submitted successfully",
            "applicationId": application_id
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "message": "Failed to submit application",
            "error": "database_error",
            "details": str(e)
        }), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# 📄 Admin — list applications (FIXED)
@application_bp.route('/', methods=['GET'])
@admin_required
def list_applications():
    status = request.args.get('status', 'pending')
    if status not in ['pending', 'approved', 'rejected']:
        return jsonify({
            "message": "Invalid status value",
            "error": "invalid_status"
        }), 400

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT a.id, a.parent_name, a.parent_email, a.child_name,
                   g.name AS grade, a.status, a.created_at
            FROM applications a
            JOIN grades g ON a.grade_id = g.id
            WHERE a.status = %s
            ORDER BY a.created_at DESC;
        """, (status,))

        # RealDictCursor returns dictionaries directly - no conversion needed
        apps = cur.fetchall()
        return jsonify(apps)

    except Exception as e:
        return jsonify({
            "message": "Failed to fetch applications",
            "error": "database_error",
            "details": str(e)
        }), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# 📄 Admin — approve
@application_bp.route('/<int:app_id>/approve', methods=['POST', 'OPTIONS'])
@admin_required
@cross_origin()
def approve_application(app_id):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Update application status
        cur.execute("""
            UPDATE applications
            SET status = 'approved'
            WHERE id = %s
            RETURNING parent_email, child_name, parent_name;
        """, (app_id,))

        result = cur.fetchone()
        if not result:
            return jsonify({
                "message": "Application not found",
                "error": "not_found"
            }), 404

        parent_email = result['parent_email']
        child_name = result['child_name']
        parent_name = result['parent_name']
        token = str(uuid.uuid4())
        expires_at = datetime.datetime.now() + datetime.timedelta(days=2)

        # Create signup token
        cur.execute("""
            INSERT INTO signup_tokens (application_id, token, expires_at)
            VALUES (%s, %s, %s);
        """, (app_id, token, expires_at))

        conn.commit()

        # Send email
        signup_link = f"http://127.0.0.1:5000/signup?token={token}"
        send_signup_email(parent_email, child_name, signup_link)

        return jsonify({
            "message": "Application approved. Signup link sent.",
            "signup_link": signup_link
        })

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "message": "Failed to approve application",
            "error": "database_error",
            "details": str(e)
        }), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# 📄 Admin — reject
@application_bp.route('/<int:app_id>/reject', methods=['POST', 'OPTIONS'])
@admin_required
@cross_origin()
def reject_application(app_id):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE applications
            SET status = 'rejected'
            WHERE id = %s
            RETURNING id;
        """, (app_id,))

        if cur.rowcount == 0:
            return jsonify({
                "message": "Application not found",
                "error": "not_found"
            }), 404

        conn.commit()
        return jsonify({"message": "Application rejected."})

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "message": "Failed to reject application",
            "error": "database_error",
            "details": str(e)
        }), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()