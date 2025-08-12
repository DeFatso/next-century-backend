import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="next_century_db",
        user="admin",
        password="clarity",
        cursor_factory=RealDictCursor  # This will return dictionaries
    )
    return conn