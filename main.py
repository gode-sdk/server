import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import uvicorn
from dotenv import load_dotenv
from pathlib import Path
import subprocess

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def connect_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logger.info("Database connection established")
        return conn, cursor
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None, None

async def lifespan(app: FastAPI):
    await startup()
    yield
    await shutdown()

async def startup():
    logger.info("Application startup")
    await run_migrations()

    conn, cursor = connect_db()
    if not conn:
        logger.error("Database connection failed, exiting.")
        return

    port = int(os.getenv("PORT", 8000))
    debug = bool(os.getenv("DEBUG", False))

    logger.info(f"Starting server on 0.0.0.0:{port}")
    if debug:
        logger.info("Running in debug mode, using 1 thread.")

async def shutdown():
    logger.info("Shutting down application")

async def run_migrations():
    logger.info("Running migrations...")
    migration_files_path = Path("migrations")
    if not migration_files_path.exists():
        logger.error("Migrations folder not found, skipping migrations.")
        return

    conn, cursor = connect_db()
    if conn:
        for migration_file in migration_files_path.iterdir():
            if migration_file.suffix == ".sql":
                with open(migration_file, "r") as file:
                    cursor.execute(file.read())
                    conn.commit()

app = FastAPI(lifespan=lifespan)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
    allow_headers=["*"],
    max_age=3600,
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the server!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
