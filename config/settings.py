"""Application settings loaded from environment variables."""

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class ElevenLabsSettings(BaseModel):
    """ElevenLabs API configuration."""

    api_key: str = ""
    model_id: str = "eleven_multilingual_v2"
    output_format: str = "mp3_44100_128"
    max_chunk_chars: int = 4500
    max_retries: int = 3
    retry_base_delay: float = 1.0


class Settings(BaseSettings):
    """MasterPi AI configuration."""

    app_name: str = "MasterPi AI"
    debug: bool = False
    log_level: str = "INFO"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # ElevenLabs
    elevenlabs: ElevenLabsSettings = ElevenLabsSettings()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_nested_delimiter": "__",
    }


settings = Settings()
