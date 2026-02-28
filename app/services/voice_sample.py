"""Extract a clean voice sample from audio for voice cloning."""

import asyncio
import logging
from pathlib import Path

from app.exceptions import PipelineError

logger = logging.getLogger(__name__)


class VoiceSampleExtractor:
    def __init__(self, sample_duration_sec: int):
        self._duration_ms = sample_duration_sec * 1000

    async def extract(self, audio_path: Path, output_dir: Path) -> Path:
        """Extract first N seconds of audio as voice sample WAV."""
        try:
            return await asyncio.to_thread(
                self._extract_sync, audio_path, output_dir
            )
        except Exception as err:
            raise PipelineError(
                message=f"Voice sample extraction failed: {err}",
                operation="extract_voice_sample",
                entity_id=str(audio_path),
            ) from err

    def _extract_sync(self, audio_path: Path, output_dir: Path) -> Path:
        from pydub import AudioSegment

        audio = AudioSegment.from_file(str(audio_path))
        sample = audio[: self._duration_ms]
        output_path = output_dir / "voice_sample.wav"
        sample.export(str(output_path), format="wav")
        logger.info(
            "Extracted %ds voice sample to %s",
            len(sample) // 1000,
            output_path.name,
        )
        return output_path
