import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    return psycopg2.connect(
        database_url,
        cursor_factory=RealDictCursor
    )
    
def init_db():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            phone VARCHAR(20),
            password TEXT NOT NULL
        )
    """)

    connection.commit()

    cursor.close()
    connection.close()