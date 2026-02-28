"""Concatenate MP3 chunks into final audiobook."""

import asyncio
import logging
from pathlib import Path

from app.exceptions import PipelineError

logger = logging.getLogger(__name__)


class AudioConcatService:
    async def concat(self, chunk_paths: list[Path], output_path: Path) -> Path:
        """Concatenate MP3 chunks into single MP3 file."""
        try:
            return await asyncio.to_thread(
                self._concat_sync, chunk_paths, output_path
            )
        except Exception as err:
            raise PipelineError(
                message=f"Audio concatenation failed: {err}",
                operation="concat_audio",
            ) from err

    def _concat_sync(self, chunk_paths: list[Path], output_path: Path) -> Path:
        from pydub import AudioSegment

        combined = AudioSegment.empty()
        for path in chunk_paths:
            segment = AudioSegment.from_mp3(str(path))
            combined += segment

        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined.export(str(output_path), format="mp3", bitrate="192k")
        logger.info(
            "Concatenated %d chunks → %s (%.1fs)",
            len(chunk_paths),
            output_path.name,
            len(combined) / 1000,
        )
        return output_path
