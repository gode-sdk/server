from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Union

import src.database.repository.mod_downloads
from src.types.api import ApiError

async def cleanup_downloads(session: AsyncSession) -> Union[None, ApiError]:
    try:
        await mod_downloads.cleanup(session)
        return None
    except SQLAlchemyError as e:
        print(f"Error cleaning up downloads: {e}")
        return ApiError.db_error()
