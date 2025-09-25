import psycopg2
import psycopg2.extras

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="next_century_db",
        user="postgres",
        password="clarity"
    )
    # Use DictCursor
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn
