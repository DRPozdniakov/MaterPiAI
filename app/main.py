"""MasterPi AI — FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.services import create_tts_service, create_voice_cloner
from app.services.tts import TTSService
from app.services.voice_cloner import VoiceCloner
from config.settings import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise shared service instances on startup."""
    app.state.voice_cloner = create_voice_cloner()
    app.state.tts_service = create_tts_service()
    logger.info("ElevenLabs services initialised")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


# ── Dependency helpers ──────────────────────────────────────────────


def get_voice_cloner(request: Request) -> VoiceCloner:
    return request.app.state.voice_cloner


def get_tts_service(request: Request) -> TTSService:
    return request.app.state.tts_service


@app.get("/")
async def root():
    return {"app": settings.app_name, "status": "running"}
