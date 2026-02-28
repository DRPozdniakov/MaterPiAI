"""ElevenLabs TTS with request stitching for long texts."""

import asyncio
import logging
from pathlib import Path

import httpx

from app.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


class TTSService:
    def __init__(self, api_key: str, base_url: str, chunk_max_chars: int):
        self._api_key = api_key
        self._base_url = base_url
        self._chunk_max = chunk_max_chars

    async def synthesize(
        self, text: str, voice_id: str, output_dir: Path
    ) -> list[Path]:
        """Synthesize text to MP3 chunks. Returns list of chunk file paths."""
        chunks = self._split_text(text)
        logger.info("TTS: %d chunks for %d chars", len(chunks), len(text))
        paths = []
        for i, chunk in enumerate(chunks):
            path = output_dir / f"tts_chunk_{i:04d}.mp3"
            await asyncio.to_thread(
                self._synthesize_chunk, chunk, voice_id, path
            )
            paths.append(path)
        return paths

    def _split_text(self, text: str) -> list[str]:
        """Split text into chunks at sentence boundaries."""
        if len(text) <= self._chunk_max:
            return [text]

        chunks = []
        current = ""
        for sentence in text.replace(". ", ".\n").split("\n"):
            if len(current) + len(sentence) + 1 > self._chunk_max and current:
                chunks.append(current.strip())
                current = sentence
            else:
                current = f"{current} {sentence}" if current else sentence
        if current.strip():
            chunks.append(current.strip())
        return chunks

    def _synthesize_chunk(self, text: str, voice_id: str, output_path: Path) -> None:
        url = f"{self._base_url}/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }
        response = httpx.post(url, headers=headers, json=payload, timeout=120.0)
        if response.status_code != 200:
            raise ExternalServiceError(
                message=f"ElevenLabs TTS returned {response.status_code}: {response.text}",
                operation="tts_synthesize",
            )
        output_path.write_bytes(response.content)
        logger.info("TTS chunk saved: %s (%d bytes)", output_path.name, len(response.content))
