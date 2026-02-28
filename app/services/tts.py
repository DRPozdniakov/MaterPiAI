"""Text-to-speech service with sentence-boundary chunking and prosody stitching."""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path

from app.exceptions import ElevenLabsError
from app.models.elevenlabs import TTSChunkResult, TTSRequest, TTSResult
from app.services.elevenlabs_client import ElevenLabsClientProvider
from config.settings import settings

logger = logging.getLogger(__name__)

# Sentence-ending punctuation (ASCII + common Unicode variants)
_SENTENCE_END = re.compile(r"(?<=[.!?。！？])\s+")


def chunk_text(text: str, max_chars: int | None = None) -> list[str]:
    """Split text into chunks on sentence boundaries, greedily packing up to max_chars.

    Pure function — no side effects.
    """
    if max_chars is None:
        max_chars = settings.elevenlabs.max_chunk_chars

    sentences = _SENTENCE_END.split(text.strip())
    sentences = [s for s in sentences if s.strip()]

    if not sentences:
        return []

    chunks: list[str] = []
    current = sentences[0]

    for sentence in sentences[1:]:
        candidate = current + " " + sentence
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current)
            current = sentence

    chunks.append(current)
    return chunks


class TTSService:
    """Generates TTS audio using ElevenLabs with prosody stitching across chunks."""

    def __init__(self, client_factory: ElevenLabsClientProvider) -> None:
        self._client_factory = client_factory

    async def generate_audio(self, request: TTSRequest) -> TTSResult:
        """Synthesize full text to an audio file.

        Chunks the text, generates each chunk sequentially (required for
        previous_request_ids stitching), then concatenates the raw bytes.
        """
        chunks = chunk_text(request.text)
        if not chunks:
            raise ElevenLabsError(
                message="No text to synthesize after chunking",
                operation="generate_audio",
            )

        client = self._client_factory.get_client(request.api_key)
        results: list[TTSChunkResult] = []
        previous_request_ids: list[str] = []

        for i, chunk in enumerate(chunks):
            logger.info("Generating TTS chunk %d/%d (%d chars)", i + 1, len(chunks), len(chunk))
            chunk_result = await self._generate_chunk(
                client=client,
                voice_id=request.voice_id,
                text=chunk,
                index=i,
                previous_request_ids=previous_request_ids[-3:],
            )
            results.append(chunk_result)
            previous_request_ids.append(chunk_result.request_id)

        # Concatenate raw audio bytes and write to file
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        total_bytes = 0
        with open(request.output_path, "wb") as f:
            for r in results:
                f.write(r.audio_bytes)
                total_bytes += len(r.audio_bytes)

        logger.info(
            "TTS complete: %d chunks, %d bytes → %s",
            len(results),
            total_bytes,
            request.output_path,
        )
        return TTSResult(
            output_path=request.output_path,
            chunks_count=len(results),
            total_bytes=total_bytes,
        )

    async def _generate_chunk(
        self,
        client,
        voice_id: str,
        text: str,
        index: int,
        previous_request_ids: list[str],
    ) -> TTSChunkResult:
        """Generate a single TTS chunk with exponential backoff retry."""
        max_retries = settings.elevenlabs.max_retries
        base_delay = settings.elevenlabs.retry_base_delay

        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                response_iter = await client.text_to_speech.with_raw_response.convert(
                    voice_id=voice_id,
                    text=text,
                    model_id=settings.elevenlabs.model_id,
                    output_format=settings.elevenlabs.output_format,
                    previous_request_ids=previous_request_ids or None,
                )
                # Unwrap the raw response
                raw_response = await response_iter.__anext__()
                request_id = raw_response.headers.get("request-id", f"chunk-{index}")

                # Collect audio bytes from the data iterator
                audio_bytes = b""
                async for chunk in raw_response.data:
                    audio_bytes += chunk

                return TTSChunkResult(
                    index=index,
                    request_id=request_id,
                    audio_bytes=audio_bytes,
                )
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    logger.warning(
                        "TTS chunk %d attempt %d failed: %s (retrying in %.1fs)",
                        index,
                        attempt + 1,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)

        raise ElevenLabsError(
            message=f"TTS chunk {index} failed after {max_retries} attempts: {last_exc}",
            operation="generate_chunk",
        ) from last_exc
