"""Pallia OS web API entrypoint."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Importing the models package registers every table on the shared metadata.
import app.models
from app.api.routes import get_router
from app.api.routes import health as health_router
from app.core.config import get_settings
from app.core.errors import AppError

logger = logging.getLogger("pallia")
settings = get_settings()


def build_error_response(status_code: int, code: str, message: str, details=None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Pallia OS - calm, minimal, enterprise-oriented operating system "
            "for home-based palliative care. Phase 1: product foundation."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return build_error_response(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(part) for part in error.get("loc", [])),
                "message": error.get("msg", ""),
            }
            for error in exc.errors()
        ]
        return build_error_response(422, "VALIDATION_ERROR", "The request data is invalid", details)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", exc_info=exc)
        return build_error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")

    # Root health endpoint (/health) and versioned API (/api/v1/...).
    app.include_router(health_router.router)
    app.include_router(get_router())

    return app


app = create_app()
