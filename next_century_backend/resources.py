from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from db import get_db_connection
import os
import datetime

resources_bp = Blueprint("resources", __name__, url_prefix="/resources")

UPLOAD_FOLDER = "uploads/resources"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@resources_bp.route("", methods=["POST"])
def upload_resource():
    title = request.form.get("title")
    description = request.form.get("description", "")
    uploaded_by = request.form.get("uploaded_by")  # e.g., admin user ID

    file = request.files.get("file")
    if not file or not title or not uploaded_by:
        return jsonify({"message": "Missing required fields"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO resources (title, description, file_url, uploaded_by)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """, (title, description, filepath, uploaded_by))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "✅ Resource uploaded"}), 201


@resources_bp.route("", methods=["GET"])
def get_resources():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, description, file_url, uploaded_at FROM resources ORDER BY uploaded_at DESC")
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


@resources_bp.route("/download/<int:resource_id>", methods=["GET"])
def download_resource(resource_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT file_url FROM resources WHERE id = %s", (resource_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"message": "File not found"}), 404

    file_path = row["file_url"]
    directory, filename = os.path.split(file_path)
    return send_from_directory(directory, filename, as_attachment=True)
