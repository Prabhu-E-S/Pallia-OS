"""Error types and the standard API error envelope.

All API errors are returned as:

    {
      "error": {
        "code": "VALIDATION_ERROR",
        "message": "Human readable message",
        "details": {}
      }
    }

Stack traces are never exposed to clients.
"""

from typing import Any


class AppError(Exception):
    """Base application error translated into a consistent API response."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", details: Any = None) -> None:
        super().__init__(message, code="NOT_FOUND", status_code=404, details=details)


class PermissionDeniedError(AppError):
    def __init__(self, message: str = "You do not have permission to do this") -> None:
        super().__init__(message, code="PERMISSION_DENIED", status_code=403)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message, code="UNAUTHORIZED", status_code=401)
