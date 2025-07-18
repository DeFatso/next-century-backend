from flask import Blueprint, jsonify, request
from db import get_db_connection
from mailer import send_signup_email
import uuid
import datetime

application_bp = Blueprint('applications', __name__)

@application_bp.route('/apply', methods=['POST'])
def apply():
    data = request.get_json()
    parent_name = data['parent_name']
    parent_email = data['parent_email']
    child_name = data['child_name']
    grade_id = data['grade_id']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO applications (parent_name, parent_email, child_name, grade_id, status)
        VALUES (%s, %s, %s, %s, 'pending') RETURNING id;
    """, (parent_name, parent_email, child_name, grade_id))
    application_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"id": application_id, "message": "Application submitted and pending approval."}), 201


@application_bp.route('/<int:app_id>/approve', methods=['POST'])
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
        cur.close()
        conn.close()
        return jsonify({"message": "Application not found"}), 404

    parent_email = result['parent_email']

    # Generate unique signup token
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



@application_bp.route('/<int:app_id>/reject', methods=['POST'])
def reject_application(app_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE applications
        SET status = 'rejected'
        WHERE id = %s;
    """, (app_id,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Application rejected."})

@application_bp.route('/pending', methods=['GET'])
def list_pending_applications():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, parent_name, parent_email, child_name, grade_id, created_at
        FROM applications
        WHERE status = 'pending'
        ORDER BY created_at DESC;
    """)
    pending_apps = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(pending_apps)

