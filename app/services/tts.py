"""ElevenLabs TTS with request stitching for long texts."""

import asyncio
import logging
import re
from pathlib import Path

import httpx

from app.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


def chunk_text(text: str, max_chars: int = 4500) -> list[str]:
    """Split text into chunks at sentence boundaries (.!?。).

    Uses forward greedy packing — accumulates sentences until adding
    the next one would exceed max_chars, then starts a new chunk.
    A single sentence longer than max_chars is kept as its own chunk.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    # Find all sentence-end positions (after .!?。 plus trailing whitespace)
    sentence_ends = [m.end() for m in re.finditer(r"[.!?。]\s*", text)]
    if not sentence_ends or sentence_ends[-1] < len(text):
        sentence_ends.append(len(text))

    chunks = []
    chunk_start = 0
    last_valid_end = chunk_start

    for end in sentence_ends:
        candidate = text[chunk_start:end].strip()
        if len(candidate) <= max_chars:
            last_valid_end = end
        else:
            if last_valid_end > chunk_start:
                chunks.append(text[chunk_start:last_valid_end].strip())
                chunk_start = last_valid_end
                # Re-evaluate current boundary from new start
                if len(text[chunk_start:end].strip()) <= max_chars:
                    last_valid_end = end
                else:
                    last_valid_end = end
            else:
                # Single sentence exceeds max_chars — keep it whole
                last_valid_end = end

    remaining = text[chunk_start:].strip()
    if remaining:
        chunks.append(remaining)

    return chunks


class TTSService:
    def __init__(self, api_key: str, base_url: str, chunk_max_chars: int, model_id: str = "eleven_multilingual_v2"):
        self._api_key = api_key
        self._base_url = base_url
        self._chunk_max = chunk_max_chars
        self._model_id = model_id

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        output_dir: Path,
        progress_cb: callable = None,
    ) -> list[Path]:
        """Synthesize text to MP3 chunks. Returns list of chunk file paths."""
        chunks = chunk_text(text, self._chunk_max)
        total = len(chunks)
        logger.info("TTS: %d chunks for %d chars", total, len(text))
        paths = []
        for i, chunk in enumerate(chunks):
            path = output_dir / f"tts_chunk_{i:04d}.mp3"
            await asyncio.to_thread(
                self._synthesize_chunk, chunk, voice_id, path
            )
            paths.append(path)
            if progress_cb:
                progress_cb(i + 1, total)
        return paths

    def _synthesize_chunk(self, text: str, voice_id: str, output_path: Path) -> None:
        url = f"{self._base_url}/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": self._model_id,
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
