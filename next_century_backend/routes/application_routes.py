from flask import Blueprint, jsonify, request
from db import get_db_connection
from mailer import send_signup_email
from functools import wraps
import uuid
import datetime

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
            return jsonify({"message": "Authentication required"}), 401
        return f(*args, **kwargs)

    return decorated


# 📄 Public — submit application
@application_bp.route('/apply', methods=['POST', 'OPTIONS'])
def apply():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    data = request.json
    parent_name = data.get("parentName")
    parent_email = data.get("email")
    child_name = data.get("childName")
    grade_name = data.get("grade")

    if not all([parent_name, parent_email, child_name, grade_name]):
        return jsonify({"message": "All fields are required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Get grade id
    cur.execute("SELECT id FROM grades WHERE name = %s", (grade_name,))
    grade_row = cur.fetchone()
    if not grade_row:
        return jsonify({"message": "Invalid grade"}), 400
    grade_id = grade_row["id"]

    # Insert application
    cur.execute("""
        INSERT INTO applications (parent_name, parent_email, child_name, grade_id, status, created_at)
        VALUES (%s, %s, %s, %s, 'pending', NOW())
    """, (parent_name, parent_email, child_name, grade_id))
    conn.commit()

    cur.close()
    conn.close()

    return jsonify({"message": "Application submitted successfully"}), 201


# 📄 Admin — list applications
@application_bp.route('/', methods=['GET', 'OPTIONS'])
@admin_required
def list_applications():
    status = request.args.get('status', 'pending')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id, a.parent_name, a.parent_email, a.child_name, g.name AS grade, a.status, a.created_at
        FROM applications a
        JOIN grades g ON a.grade_id = g.id
        WHERE a.status = %s
        ORDER BY a.created_at DESC;
    """, (status,))
    apps = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(apps)


# 📄 Admin — approve
@application_bp.route('/<int:app_id>/approve', methods=['POST', 'OPTIONS'])
@admin_required
def approve_application(app_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE applications
        SET status = 'approved'
        WHERE id = %s
        RETURNING parent_email;
    """, (app_id,))
    result = cur.fetchone()
    if not result:
        return jsonify({"message": "Application not found"}), 404

    parent_email = result['parent_email']
    token = str(uuid.uuid4())
    expires_at = datetime.datetime.now() + datetime.timedelta(days=2)

    cur.execute("""
        INSERT INTO signup_tokens (application_id, token, expires_at)
        VALUES (%s, %s, %s);
    """, (app_id, token, expires_at))
    conn.commit()
    cur.close()
    conn.close()

    signup_link = f"http://127.0.0.1:5000/signup?token={token}"
    send_signup_email(parent_email, signup_link)

    print(f"✅ Signup link for {parent_email}: {signup_link}")

    return jsonify({"message": "Application approved. Signup link sent.", "signup_link": signup_link})


# 📄 Admin — reject
@application_bp.route('/<int:app_id>/reject', methods=['POST', 'OPTIONS'])
@admin_required
def reject_application(app_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE applications
        SET status = 'rejected'
        WHERE id = %s;
    """, (app_id,))
    if cur.rowcount == 0:
        return jsonify({"message": "Application not found"}), 404
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Application rejected."})
