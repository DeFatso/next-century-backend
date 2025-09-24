from flask import request, jsonify
from datetime import datetime
from db import get_db_connection
from . import teacher_bp

# ---------------------------
# POST: Add a Lesson
# ---------------------------
@teacher_bp.route("/lessons", methods=["POST"])
def add_lesson():
    data = request.get_json()
    print("Received lesson data:", data)  # debug

    teacher_id = data.get("teacher_id")
    title = data.get("title")
    description = data.get("description")
    grade_id = data.get("grade_id")
    zoom_link = data.get("zoom_link", "")
    youtube_link = data.get("youtube_link", "")

    # validate required fields
    if not all([teacher_id, title, description, grade_id]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check if teacher exists
        cur.execute("SELECT id FROM users WHERE id = %s AND role = 'teacher'", (teacher_id,))
        teacher = cur.fetchone()
        if not teacher:
            return jsonify({"error": "Teacher not found"}), 404

        # Check if grade exists
        cur.execute("SELECT id FROM grades WHERE id = %s", (grade_id,))
        grade = cur.fetchone()
        if not grade:
            return jsonify({"error": "Grade not found"}), 404

        # INSERT the lesson
        cur.execute("""
            INSERT INTO lessons (created_by, title, description, grade_id, zoom_link, youtube_link, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            teacher_id,
            title,
            description,
            grade_id,
            zoom_link,
            youtube_link,
            datetime.utcnow(),
            datetime.utcnow()
        ))

        lesson_id_row = cur.fetchone()
        if lesson_id_row is None:
            raise Exception("Failed to insert lesson")

        # FIX: Use dictionary access instead of tuple index
        lesson_id = lesson_id_row["id"] if isinstance(lesson_id_row, dict) else lesson_id_row[0]

        conn.commit()

        return jsonify({
            "message": "Lesson created successfully",
            "lesson_id": lesson_id
        }), 201

    except Exception as e:
        conn.rollback()
        import traceback
        print("Error details:", traceback.format_exc())
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    finally:
        cur.close()
        conn.close()

# READ lessons for dashboard
@teacher_bp.route("/dashboard/<int:teacher_id>", methods=["GET"])
def dashboard(teacher_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if teacher exists first
        cur.execute("SELECT id FROM users WHERE id = %s AND role = 'teacher'", (teacher_id,))
        teacher = cur.fetchone()
        if not teacher:
            return jsonify({"error": "Teacher not found"}), 404

        cur.execute("""
            SELECT id, title, description, grade_id, zoom_link, youtube_link
            FROM lessons
            WHERE created_by=%s
            ORDER BY id
        """, (teacher_id,))
        lessons = cur.fetchall()

        lesson_list = []
        for l in lessons:
            lesson_list.append({
                "id": l["id"] if isinstance(l, dict) else l[0],
                "title": l["title"] if isinstance(l, dict) else l[1],
                "description": l["description"] if isinstance(l, dict) else l[2],
                "grade_id": l["grade_id"] if isinstance(l, dict) else l[3],
                "zoom_link": l["zoom_link"] if isinstance(l, dict) else l[4],
                "youtube_link": l["youtube_link"] if isinstance(l, dict) else l[5]
            })

        return jsonify({"teacher_id": teacher_id, "lessons": lesson_list})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    finally:
        cur.close()
        conn.close()

# UPDATE lesson
@teacher_bp.route("/lessons/<int:lesson_id>", methods=["PUT"])
def edit_lesson(lesson_id):
    data = request.get_json()
    title = data.get("title")
    description = data.get("description")
    grade_id = data.get("grade_id")
    zoom_link = data.get("zoom_link", "")
    youtube_link = data.get("youtube_link", "")

    if not all([title, description, grade_id]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check if lesson exists
        cur.execute("SELECT id FROM lessons WHERE id = %s", (lesson_id,))
        lesson = cur.fetchone()
        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        cur.execute("""
            UPDATE lessons
            SET title=%s, description=%s, grade_id=%s, zoom_link=%s, youtube_link=%s, updated_at=%s
            WHERE id=%s
        """, (title, description, grade_id, zoom_link, youtube_link, datetime.utcnow(), lesson_id))
        
        conn.commit()
        return jsonify({"message": "Lesson updated successfully"})
    
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
        
    finally:
        cur.close()
        conn.close()

# DELETE lesson
@teacher_bp.route("/lessons/<int:lesson_id>", methods=["DELETE"])
def delete_lesson(lesson_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check if lesson exists
        cur.execute("SELECT id FROM lessons WHERE id = %s", (lesson_id,))
        lesson = cur.fetchone()
        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        cur.execute("DELETE FROM lessons WHERE id=%s", (lesson_id,))
        conn.commit()
        return jsonify({"message": "Lesson deleted successfully"})
    
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
        
    finally:
        cur.close()
        conn.close()