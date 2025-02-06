# api.py

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from pydantic import BaseModel
from typing import Generic, TypeVar, List
from pydantic import BaseModel

# Generic type for paginated data and responses.
T = TypeVar("T")

class PaginatedData(BaseModel, Generic[T]):
    data: List[T]
    count: int

class ApiResponse(BaseModel, Generic[T]):
    error: str
    payload: T

class ApiError(Exception):
    """
    Custom API error with an associated error type.
    """
    def __init__(self, message: str = "", error_type: str = "InternalError"):
        self.message = message
        self.error_type = error_type
        super().__init__(message)

    def __str__(self):
        if self.error_type == "FilesystemError":
            return "Unknown filesystem error"
        elif self.error_type == "DbAcquireError":
            return "Database is busy"
        elif self.error_type == "DbError":
            return "Unknown database error"
        elif self.error_type == "TransactionError":
            return "Unknown transaction error"
        elif self.error_type == "BadRequest":
            return self.message or "Bad Request"
        elif self.error_type == "NotFound":
            return self.message or "Not Found"
        elif self.error_type == "Unauthorized":
            return "You need to be authenticated to perform this action"
        elif self.error_type == "Forbidden":
            return "You cannot perform this action"
        else:
            return "Internal server error"

def api_exception_handler(request: Request, exc: ApiError):
    """
    FastAPI exception handler for ApiError.
    """
    # Choose status code based on error type
    status_code = HTTP_500_INTERNAL_SERVER_ERROR
    if exc.error_type == "BadRequest":
        status_code = HTTP_400_BAD_REQUEST
    elif exc.error_type == "NotFound":
        status_code = HTTP_404_NOT_FOUND
    elif exc.error_type == "Unauthorized":
        status_code = HTTP_401_UNAUTHORIZED
    elif exc.error_type == "Forbidden":
        status_code = HTTP_403_FORBIDDEN

    return JSONResponse(
        status_code=status_code,
        content={"error": str(exc), "payload": ""}
    )

def query_error_handler(err: Exception, request: Request):
    """
    Converts a query payload error into an API error.
    """
    return api_exception_handler(request, ApiError(str(err), error_type="BadRequest"))

def create_download_link(app_url: str, mod_id: str, version: str) -> str:
    """
    Create a download link in the format:
      {app_url}/v1/mods/{mod_id}/versions/{version}/download
    """
    return f"{app_url}/v1/mods/{mod_id}/versions/{version}/download"
