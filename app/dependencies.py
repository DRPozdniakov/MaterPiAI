"""Service factories for FastAPI Depends()."""

from functools import lru_cache

from config.settings import settings
from app.services.audio_concat import AudioConcatService
from app.services.cost_calculator import CostCalculator
from app.services.job_manager import JobManager
from app.services.pipeline import PipelineOrchestrator
from app.services.transcriber import TranscriberService
from app.services.translator import TranslatorService
from app.services.tts import TTSService
from app.services.voice_cloner import VoiceClonerService
from app.services.voice_sample import VoiceSampleExtractor
from app.services.youtube import YouTubeService


@lru_cache
def get_youtube_service() -> YouTubeService:
    return YouTubeService(output_dir=settings.output_dir)


@lru_cache
def get_cost_calculator() -> CostCalculator:
    return CostCalculator(
        cost_per_min_whisper=settings.cost_per_min_whisper,
        cost_per_min_translation=settings.cost_per_min_translation,
        cost_per_min_tts=settings.cost_per_min_tts,
        cost_per_min_voice_clone=settings.cost_per_min_voice_clone,
        platform_margin=settings.platform_margin,
        tier_short_min=settings.tier_short_min,
        tier_medium_min=settings.tier_medium_min,
    )


@lru_cache
def get_transcriber_service() -> TranscriberService:
    return TranscriberService(
        model_size=settings.whisper_model,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
    )


@lru_cache
def get_voice_sample_extractor() -> VoiceSampleExtractor:
    return VoiceSampleExtractor(sample_duration_sec=settings.voice_sample_duration_sec)


@lru_cache
def get_voice_cloner_service() -> VoiceClonerService:
    return VoiceClonerService(
        api_key=settings.elevenlabs_api_key,
        base_url=settings.elevenlabs_base_url,
    )


@lru_cache
def get_translator_service() -> TranslatorService:
    return TranslatorService(api_key=settings.anthropic_api_key)


@lru_cache
def get_tts_service() -> TTSService:
    return TTSService(
        api_key=settings.elevenlabs_api_key,
        base_url=settings.elevenlabs_base_url,
        chunk_max_chars=settings.tts_chunk_max_chars,
    )


@lru_cache
def get_audio_concat_service() -> AudioConcatService:
    return AudioConcatService()


@lru_cache
def get_job_manager() -> JobManager:
    return JobManager()


@lru_cache
def get_pipeline() -> PipelineOrchestrator:
    return PipelineOrchestrator(
        youtube=get_youtube_service(),
        transcriber=get_transcriber_service(),
        voice_sample=get_voice_sample_extractor(),
        voice_cloner=get_voice_cloner_service(),
        translator=get_translator_service(),
        tts=get_tts_service(),
        audio_concat=get_audio_concat_service(),
        cost_calculator=get_cost_calculator(),
        job_manager=get_job_manager(),
        output_dir=settings.output_dir,
    )
