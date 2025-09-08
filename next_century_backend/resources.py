from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from db import get_db_connection
import os
import psycopg2.extras

resources_bp = Blueprint("resources", __name__, url_prefix="/resources")

UPLOAD_FOLDER = "uploads/resources"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Upload resource ---
@resources_bp.route("", methods=["POST"])
def upload_resource():
    """
    Upload a resource.
    Supports JSON or form-data.
    """
    if request.is_json:
        data = request.get_json()
        title = data.get("title")
        description = data.get("description", "")
        uploaded_by = data.get("uploaded_by")
        grade_id = data.get("grade_id")  # NEW: grade for the resource
        file_url = data.get("file_url")  # Must be provided in JSON mode

        if not title or not uploaded_by or not file_url or not grade_id:
            return jsonify({"message": "Missing required fields"}), 400

    else:
        title = request.form.get("title")
        description = request.form.get("description", "")
        uploaded_by = request.form.get("uploaded_by")
        grade_id = request.form.get("grade_id")
        file = request.files.get("file")

        if not title or not uploaded_by or not file or not grade_id:
            return jsonify({"message": "Missing required fields"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        file_url = filepath

    # Insert into DB
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO resources (title, description, file_url, uploaded_by, grade_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """, (title, description, file_url, uploaded_by, grade_id))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "✅ Resource uploaded"}), 201


# --- Get resources ---
@resources_bp.route("", methods=["GET"])
def get_resources():
    grade_id = request.args.get("grade_id")  # e.g., /resources?grade_id=3

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if grade_id:
        cur.execute("""
            SELECT id, title, description, file_url, uploaded_at
            FROM resources
            WHERE grade_id = %s
            ORDER BY uploaded_at DESC
        """, (grade_id,))
    else:
        cur.execute("""
            SELECT id, title, description, file_url, uploaded_at
            FROM resources
            ORDER BY uploaded_at DESC
        """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    resources = [
        {
            "id": r["id"],
            "title": r["title"],
            "description": r["description"],
            "file_url": f"/resources/download/{r['id']}",
            "uploaded_at": r["uploaded_at"]
        }
        for r in rows
    ]

    return jsonify(resources)


# --- Download resource ---
@resources_bp.route("/download/<int:resource_id>", methods=["GET"])
def download_resource(resource_id):
    """
    Download a resource file by ID
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT file_url FROM resources WHERE id = %s", (resource_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"message": "File not found"}), 404

    file_path = row["file_url"]
    if not os.path.exists(file_path):
        return jsonify({"message": "File missing on server"}), 404

    directory, filename = os.path.split(file_path)
    return send_from_directory(directory, filename, as_attachment=True)
