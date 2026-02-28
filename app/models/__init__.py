"""Pydantic DTOs for MasterPi AI API."""

from enum import Enum

from pydantic import BaseModel, HttpUrl


class Tier(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    FULL = "full"


class JobStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    EXTRACTING_VOICE = "extracting_voice"
    CLONING_VOICE = "cloning_voice"
    TRANSLATING = "translating"
    SYNTHESIZING = "synthesizing"
    CONCATENATING = "concatenating"
    COMPLETED = "completed"
    FAILED = "failed"


# --- Requests ---


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class CreateJobRequest(BaseModel):
    url: HttpUrl
    tier: Tier
    target_language: str


# --- Responses ---


class TierCost(BaseModel):
    tier: Tier
    duration_minutes: float
    transcription_cost: float
    translation_cost: float
    tts_cost: float
    stripe_fee: float
    total_cost: float


class VideoInfo(BaseModel):
    title: str
    channel: str
    duration_seconds: int
    thumbnail_url: str = ""


class AnalyzeResponse(BaseModel):
    video: VideoInfo
    tiers: list[TierCost]


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress_pct: int = 0
    current_stage: str = ""
    error: str | None = None


class LanguageResponse(BaseModel):
    code: str
    name: str


class SSEEvent(BaseModel):
    status: JobStatus
    progress_pct: int
    current_stage: str
    error: str | None = None
