"""Service factory wiring for ElevenLabs integration."""

from app.services.elevenlabs_client import ElevenLabsClientFactory
from app.services.tts import TTSService
from app.services.voice_cloner import VoiceCloner


def create_voice_cloner() -> VoiceCloner:
    """Create a VoiceCloner with the default client factory."""
    return VoiceCloner(ElevenLabsClientFactory())


def create_tts_service() -> TTSService:
    """Create a TTSService with the default client factory."""
    return TTSService(ElevenLabsClientFactory())
