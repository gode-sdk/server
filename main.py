
import psycopg2
from dotenv import load_dotenv
import os
import time


load_dotenv()


# Database connection parameters
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}


def connect():
    """Establishes a database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None, None


def create_table():
    """Creates a users table if it doesn't exist."""
    conn, cursor = connect()
    if not conn:
        return
    query = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        age INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()
    print("Table created successfully.")


def insert_user(name, email, age):
    """Inserts a user into the database."""
    conn, cursor = connect()
    if not conn:
        return

    query = """
    INSERT INTO users (name, email, age) VALUES (%s, %s, %s)
    RETURNING id;
    """
    try:
        cursor.execute(query, (name, email, age))
        user_id = cursor.fetchone()[0]
        conn.commit()
        print(f"User inserted with ID: {user_id}")
    except Exception as e:
        print(f"Error inserting user: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def get_users():
    """Fetches all users from the database."""
    conn, cursor = connect()
    if not conn:
        return

    query = "SELECT * FROM users;"
    cursor.execute(query)
    users = cursor.fetchall()
    for user in users:
        print(user)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    # Wait for PostgreSQL to be ready
    time.sleep(10)  # Adjust depending on your system

    create_table()
    insert_user("John Doe", "john@example.com", 30)
    get_users()
