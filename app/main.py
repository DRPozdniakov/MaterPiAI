"""MasterPi AI — FastAPI application entry point."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router as health_router
from app.api.language_routes import router as language_router
from app.api.video_routes import router as video_router
from app.api.job_routes import router as job_router
from app.exceptions import MasterPiAIException, ValidationError
from config.settings import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(language_router, prefix="/api/v1")
app.include_router(video_router, prefix="/api/v1")
app.include_router(job_router, prefix="/api/v1")


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": exc.message,
            "operation": exc.operation,
            "entity_id": exc.entity_id,
        },
    )


@app.exception_handler(MasterPiAIException)
async def app_error_handler(request: Request, exc: MasterPiAIException):
    logger.error("App error: %s [op=%s]", exc.message, exc.operation)
    return JSONResponse(
        status_code=500,
        content={
            "error": type(exc).__name__,
            "message": exc.message,
            "operation": exc.operation,
            "entity_id": exc.entity_id,
        },
    )


@app.get("/")
async def root():
    return {"app": settings.app_name, "status": "running"}
