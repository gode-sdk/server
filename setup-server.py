import psycopg2
from dotenv import load_dotenv
import os
import argparse
from pathlib import Path

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def connect():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None, None

def setup(cursor, conn):
    file_path = Path("./default.sql")
    query = ""
    
    if file_path.exists():
        query = file_path.read_text(encoding="utf-8")
        cursor.execute(query)
        conn.commit()
        print("Table created successfully.")
    else:
        print("SQL file not found!")

def clear(cursor, conn):
    # Query to get all table names excluding system tables
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public';
    """)
    
    tables = cursor.fetchall()
    
    if tables:
        for table in tables:
            table_name = table[0]
            drop_query = f"DROP TABLE IF EXISTS {table_name} CASCADE;"
            cursor.execute(drop_query)
            print(f"Dropped table: {table_name}")
        conn.commit()
    else:
        print("No tables to drop.")

def main():
    # Set up argparse
    parser = argparse.ArgumentParser(description="Database setup and management script")
    
    # Define available commands
    parser.add_argument(
        "command", 
        choices=["setup", "clear", "both"], 
        help="Command to execute: 'setup', 'clear', or 'both'."
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Connect to the database
    conn, cursor = connect()
    if not conn:
        return
    
    # Run the appropriate command based on the user's input
    if args.command == "setup":
        setup(cursor, conn)
    elif args.command == "clear":
        clear(cursor, conn)
    elif args.command == "both":
        clear(cursor, conn)
        setup(cursor, conn)
    
    # Close the cursor and connection
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
