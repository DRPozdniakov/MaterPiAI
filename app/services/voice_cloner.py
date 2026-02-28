"""Voice cloning service with managed lifecycle."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from app.exceptions import ElevenLabsError
from app.models.elevenlabs import VoiceCloneRequest, VoiceCloneResult
from app.services.elevenlabs_client import ElevenLabsClientProvider

logger = logging.getLogger(__name__)


class VoiceCloner:
    """Handles voice clone creation and deletion via the ElevenLabs API."""

    def __init__(self, client_factory: ElevenLabsClientProvider) -> None:
        self._client_factory = client_factory

    async def clone_voice(self, request: VoiceCloneRequest) -> VoiceCloneResult:
        """Create an instant voice clone from an audio sample."""
        client = self._client_factory.get_client(request.api_key)
        try:
            with open(request.sample_path, "rb") as f:
                response = await client.voices.ivc.create(
                    name=request.name,
                    files=[f],
                    description=request.description or None,
                )
            logger.info("Cloned voice %r → %s", request.name, response.voice_id)
            return VoiceCloneResult(voice_id=response.voice_id, name=request.name)
        except Exception as exc:
            raise ElevenLabsError(
                message=f"Voice cloning failed: {exc}",
                operation="clone_voice",
            ) from exc

    async def delete_voice(self, voice_id: str, api_key: str | None = None) -> None:
        """Delete a cloned voice. Failure is logged but not raised."""
        client = self._client_factory.get_client(api_key)
        try:
            await client.voices.delete(voice_id=voice_id)
            logger.info("Deleted cloned voice %s", voice_id)
        except Exception:
            logger.warning("Failed to delete voice %s (non-fatal)", voice_id, exc_info=True)

    @asynccontextmanager
    async def managed_voice(
        self, request: VoiceCloneRequest
    ) -> AsyncIterator[VoiceCloneResult]:
        """Context manager that clones a voice and guarantees cleanup.

        Usage::

            async with cloner.managed_voice(req) as voice:
                await tts.generate_audio(voice.voice_id, ...)
            # voice deleted automatically here
        """
        result = await self.clone_voice(request)
        try:
            yield result
        finally:
            await self.delete_voice(result.voice_id, api_key=request.api_key)
