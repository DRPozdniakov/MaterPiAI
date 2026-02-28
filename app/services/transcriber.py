"""Speech-to-text transcription via faster-whisper."""

import asyncio
import logging
from pathlib import Path

from app.exceptions import PipelineError

logger = logging.getLogger(__name__)


class TranscriberService:
    def __init__(self, model_size: str, device: str, compute_type: str):
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model = None

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            logger.info(
                "Loading whisper model=%s device=%s",
                self._model_size,
                self._device,
            )
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
            )
        return self._model

    async def transcribe(self, audio_path: Path) -> str:
        """Transcribe audio file to text. Returns full transcript string."""
        try:
            return await asyncio.to_thread(self._transcribe_sync, audio_path)
        except Exception as err:
            raise PipelineError(
                message=f"Transcription failed: {err}",
                operation="transcribe",
                entity_id=str(audio_path),
            ) from err

    def _transcribe_sync(self, audio_path: Path) -> str:
        model = self._get_model()
        segments, _ = model.transcribe(str(audio_path), beam_size=5)
        parts = [segment.text.strip() for segment in segments]
        transcript = " ".join(parts)
        logger.info("Transcribed %d characters from %s", len(transcript), audio_path.name)
        return transcript
