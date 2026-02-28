"""ElevenLabs instant voice clone via REST API (httpx)."""

import asyncio
import logging
from pathlib import Path

import httpx

from app.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


class VoiceClonerService:
    def __init__(self, api_key: str, base_url: str):
        self._api_key = api_key
        self._base_url = base_url

    async def clone_voice(self, sample_path: Path, name: str) -> str:
        """Clone voice from sample. Returns ElevenLabs voice_id."""
        try:
            return await asyncio.to_thread(
                self._clone_sync, sample_path, name
            )
        except ExternalServiceError:
            raise
        except Exception as err:
            raise ExternalServiceError(
                message=f"Voice cloning failed: {err}",
                operation="clone_voice",
            ) from err

    def _clone_sync(self, sample_path: Path, name: str) -> str:
        url = f"{self._base_url}/voices/add"
        headers = {"xi-api-key": self._api_key}
        with open(sample_path, "rb") as f:
            files = [("files", (sample_path.name, f, "audio/wav"))]
            data = {"name": name, "description": "Auto-cloned for audiobook"}
            response = httpx.post(
                url, headers=headers, data=data, files=files, timeout=60.0
            )
        if response.status_code != 200:
            raise ExternalServiceError(
                message=f"ElevenLabs voice clone returned {response.status_code}: {response.text}",
                operation="clone_voice",
            )
        voice_id = response.json()["voice_id"]
        logger.info("Cloned voice: %s", voice_id)
        return voice_id

    async def delete_voice(self, voice_id: str) -> None:
        """Cleanup cloned voice after job completes."""
        try:
            url = f"{self._base_url}/voices/{voice_id}"
            headers = {"xi-api-key": self._api_key}
            async with httpx.AsyncClient() as client:
                await client.delete(url, headers=headers, timeout=30.0)
            logger.info("Deleted cloned voice: %s", voice_id)
        except Exception as err:
            logger.warning("Failed to delete voice %s: %s", voice_id, err)
