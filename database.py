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

    # =========================
    # USERS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            phone VARCHAR(20),
            password TEXT NOT NULL
        )
    """)

    # =========================
    # ACCIDENTS TABLE
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accidents (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL,
            status VARCHAR(50) DEFAULT 'Detected',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()

    cursor.close()
    connection.close()