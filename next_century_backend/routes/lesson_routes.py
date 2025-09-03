from flask import Blueprint, jsonify, request
from db import get_db_connection
from functools import wraps
from flask_cors import cross_origin
import datetime

# Create lesson blueprint
lesson_bp = Blueprint('lessons', __name__, url_prefix='/lessons')

# Admin required decorator (reuse from admin_routes or create here)
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == 'admin' and auth.password == 'supersecret'):
            return jsonify({
                "message": "Authentication required",
                "error": "invalid_credentials"
            }), 401
        return f(*args, **kwargs)
    return decorated

# Get all lessons
@lesson_bp.route('/', methods=['GET'])
@cross_origin()
def get_lessons():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                l.id, l.title, l.content_text, l.video_url, l.created_at,
                s.name as subject_name, g.name as grade_name,
                u.full_name as created_by_name
            FROM lessons l
            JOIN subjects s ON l.subject_id = s.id
            JOIN grades g ON s.grade_id = g.id
            LEFT JOIN users u ON l.created_by = u.id
            ORDER BY l.created_at DESC
        """)
        
        lessons = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(lessons)
        
    except Exception as e:
        return jsonify({
            "message": "Failed to fetch lessons",
            "error": "database_error",
            "details": str(e)
        }), 500

# Get single lesson
@lesson_bp.route('/<int:lesson_id>', methods=['GET'])
def get_lesson(lesson_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                l.*, s.name as subject_name, g.name as grade_name,
                u.full_name as created_by_name
            FROM lessons l
            JOIN subjects s ON l.subject_id = s.id
            JOIN grades g ON s.grade_id = g.id
            LEFT JOIN users u ON l.created_by = u.id
            WHERE l.id = %s
        """, (lesson_id,))
        
        lesson = cur.fetchone()
        cur.close()
        conn.close()
        
        if not lesson:
            return jsonify({
                "message": "Lesson not found",
                "error": "not_found"
            }), 404
        
        return jsonify(lesson)
        
    except Exception as e:
        return jsonify({
            "message": "Failed to fetch lesson",
            "error": "database_error",
            "details": str(e)
        }), 500

# routes/lesson_routes.py - Update create_lesson function
@lesson_bp.route('/grade/<int:grade_id>', methods=['POST'])
@cross_origin()
@admin_required
def create_lesson_for_grade(grade_id):
    try:
        data = request.get_json()
        
        required_fields = ['title', 'subject_id', 'content_text']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "message": f"Missing required field: {field}",
                    "error": "missing_field"
                }), 400
        
        # Verify subject belongs to the specified grade
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM subjects WHERE id = %s AND grade_id = %s", 
                   (data['subject_id'], grade_id))
        subject = cur.fetchone()
        
        if not subject:
            return jsonify({
                "message": "Subject does not belong to the specified grade",
                "error": "invalid_subject"
            }), 400
        
        cur.execute("""
            INSERT INTO lessons (title, subject_id, content_text, video_url, created_by)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data['title'],
            data['subject_id'],
            data['content_text'],
            data.get('video_url'),
            data.get('created_by')
        ))
        
        lesson_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "message": "Lesson created successfully for grade",
            "lesson_id": lesson_id
        }), 201
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "message": "Failed to create lesson",
            "error": "database_error",
            "details": str(e)
        }), 500

# Update lesson (admin only)
@lesson_bp.route('/<int:lesson_id>', methods=['PUT'])
@admin_required
def update_lesson(lesson_id):
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if lesson exists
        cur.execute("SELECT id FROM lessons WHERE id = %s", (lesson_id,))
        if not cur.fetchone():
            return jsonify({
                "message": "Lesson not found",
                "error": "not_found"
            }), 404
        
        # Build update query dynamically
        update_fields = []
        update_values = []
        
        if 'title' in data:
            update_fields.append("title = %s")
            update_values.append(data['title'])
        if 'subject_id' in data:
            update_fields.append("subject_id = %s")
            update_values.append(data['subject_id'])
        if 'content_text' in data:
            update_fields.append("content_text = %s")
            update_values.append(data['content_text'])
        if 'video_url' in data:
            update_fields.append("video_url = %s")
            update_values.append(data['video_url'])
        
        if not update_fields:
            return jsonify({
                "message": "No fields to update",
                "error": "no_update"
            }), 400
        
        update_values.append(lesson_id)
        update_query = f"""
            UPDATE lessons 
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE id = %s
            RETURNING id
        """
        
        cur.execute(update_query, update_values)
        conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({
            "message": "Lesson updated successfully",
            "lesson_id": lesson_id
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "message": "Failed to update lesson",
            "error": "database_error",
            "details": str(e)
        }), 500

# Delete lesson (admin only)
@lesson_bp.route('/<int:lesson_id>', methods=['DELETE'])
@admin_required
def delete_lesson(lesson_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if lesson exists
        cur.execute("SELECT id FROM lessons WHERE id = %s", (lesson_id,))
        if not cur.fetchone():
            return jsonify({
                "message": "Lesson not found",
                "error": "not_found"
            }), 404
        
        cur.execute("DELETE FROM lessons WHERE id = %s", (lesson_id,))
        conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({
            "message": "Lesson deleted successfully",
            "deleted_lesson_id": lesson_id
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "message": "Failed to delete lesson",
            "error": "database_error",
            "details": str(e)
        }), 500

# Get lessons by subject
@lesson_bp.route('/subject/<int:subject_id>', methods=['GET'])
def get_lessons_by_subject(subject_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                l.id, l.title, l.content_text, l.video_url, l.created_at,
                s.name as subject_name, g.name as grade_name
            FROM lessons l
            JOIN subjects s ON l.subject_id = s.id
            JOIN grades g ON s.grade_id = g.id
            WHERE l.subject_id = %s
            ORDER BY l.created_at DESC
        """, (subject_id,))
        
        lessons = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(lessons)
        
    except Exception as e:
        return jsonify({
            "message": "Failed to fetch lessons",
            "error": "database_error",
            "details": str(e)
        }), 500