"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """MasterPi AI configuration."""

    app_name: str = "MasterPi AI"
    debug: bool = False
    log_level: str = "INFO"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # External services
    elevenlabs_api_key: str = ""
    anthropic_api_key: str = ""

    # ElevenLabs TTS
    elevenlabs_base_url: str = "https://api.elevenlabs.io/v1"
    elevenlabs_model_id: str = "eleven_multilingual_v2"
    tts_chunk_max_chars: int = 4500

    # Voice sample
    voice_sample_duration_sec: int = 45

    # Default voice ID — used when voice cloning is unavailable
    elevenlabs_default_voice_id: str = "21m00Tcm4TlvDq8ikWAM"

    # Cost per minute (USD) — for pricing display
    cost_per_min_whisper: float = 0.0        # local faster-whisper, no API cost
    cost_per_min_translation: float = 0.022  # Claude Sonnet chunked (~20% overhead for context)
    cost_per_min_tts: float = 0.10           # ElevenLabs ~1000 chars/min
    cost_per_min_voice_clone: float = 0.0    # included in ElevenLabs plan
    platform_margin: float = 0.25            # 25% markup

    # Stripe fee
    stripe_fee_pct: float = 0.029            # 2.9%
    stripe_fee_fixed: float = 0.30           # $0.30 per transaction

    # Tier duration as fraction of full video
    tier_short_fraction: float = 0.125   # 12.5% → Full is 8x Short
    tier_medium_fraction: float = 0.40   # 40%   → Full is 2.5x Medium

    # CORS — comma-separated origins in env, parsed to list
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:8080"

    # Demo mode — cap all downloads to N seconds (0 = use real tier duration)
    demo_max_seconds: int = 60

    # Output
    output_dir: str = "output"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
