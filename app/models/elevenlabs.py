"""Pydantic schemas for ElevenLabs voice cloning and TTS."""

from pathlib import Path

from pydantic import BaseModel, Field


class VoiceCloneRequest(BaseModel):
    """Request to clone a voice from an audio sample."""

    name: str = Field(description="Display name for the cloned voice")
    sample_path: Path = Field(description="Path to the audio sample (30-45s recommended)")
    description: str = ""
    api_key: str | None = Field(
        default=None, description="Per-request API key; falls back to env config"
    )


class VoiceCloneResult(BaseModel):
    """Result of a successful voice clone."""

    voice_id: str
    name: str


class TTSRequest(BaseModel):
    """Request to synthesize text with a cloned voice."""

    text: str = Field(description="Full text to synthesize (will be chunked internally)")
    voice_id: str
    output_path: Path = Field(description="Where to write the final audio file")
    api_key: str | None = Field(
        default=None, description="Per-request API key; falls back to env config"
    )


class TTSChunkResult(BaseModel):
    """Result for a single TTS chunk."""

    index: int
    request_id: str
    audio_bytes: bytes

    model_config = {"arbitrary_types_allowed": True}


class TTSResult(BaseModel):
    """Result of full TTS generation."""

    output_path: Path
    chunks_count: int
    total_bytes: int
