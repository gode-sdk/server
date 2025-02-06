import asyncio
import logging
from alembic.config import Config
from alembic import command
from asyncpg import connect
from src.config import AppData

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate(app_data: AppData):
    try:
        # You can connect to the database using asyncpg
        conn = await connect(dsn=app_data.db_url)  # Replace with actual connection string from AppData

        # Run migrations with Alembic
        alembic_cfg = Config("alembic.ini")  # Assuming you have alembic.ini in your project root
        command.upgrade(alembic_cfg, "head")  # Run migrations to the latest version

        logger.info("Database migration completed successfully.")

    except Exception as e:
        logger.error(f"Error encountered while running migrations: {e}")
    finally:
        await conn.close()

# Usage in main async function:
# await migrate(app_data)
