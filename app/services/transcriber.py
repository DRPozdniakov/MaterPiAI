"""Extract transcript from YouTube subtitles via yt-dlp."""

import asyncio
import logging
import re
import tempfile
import time
from pathlib import Path

from app.exceptions import PipelineError

logger = logging.getLogger(__name__)


class TranscriberService:
    async def transcribe(self, url: str, max_duration_sec: int | None = None) -> str:
        """Extract transcript from YouTube subtitles. Returns plain text."""
        try:
            return await asyncio.to_thread(self._extract_subs, url, max_duration_sec)
        except PipelineError:
            raise
        except Exception as err:
            raise PipelineError(
                message=f"Subtitle extraction failed: {err}",
                operation="transcribe",
                entity_id=url,
            ) from err

    def _extract_subs(self, url: str, max_duration_sec: int | None) -> str:
        import yt_dlp

        # Retry the whole download up to 3 times with increasing backoff
        for attempt in range(3):
            try:
                raw = self._try_download_subs(url)
                if raw:
                    text = self._parse_subtitle_text(raw, max_duration_sec)
                    logger.info("Extracted %d characters of transcript", len(text))
                    return text
            except Exception as err:
                if "429" in str(err) and attempt < 2:
                    wait = 5 * (attempt + 1)
                    logger.warning("YouTube 429, waiting %ds before retry %d/3", wait, attempt + 2)
                    time.sleep(wait)
                    continue
                raise

        raise PipelineError(
            message="No subtitles available for this video",
            operation="transcribe",
            entity_id=url,
        )

    def _try_download_subs(self, url: str) -> str | None:
        import yt_dlp

        with tempfile.TemporaryDirectory() as tmpdir:
            out_tmpl = str(Path(tmpdir) / "subs")

            opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["en", "en-orig", "en-US"],
                "subtitlesformat": "vtt",
                "outtmpl": out_tmpl,
                "retries": 3,
                "extractor_retries": 3,
                "ignoreerrors": True,
                "sleep_interval_subtitles": 2,
                            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            # Find any downloaded subtitle file
            sub_files = list(Path(tmpdir).glob("*.vtt"))
            if not sub_files:
                sub_files = list(Path(tmpdir).glob("subs*"))

            if not sub_files:
                return None

            return sub_files[0].read_text(encoding="utf-8")

    def _parse_subtitle_text(self, raw: str, max_duration_sec: int | None) -> str:
        """Strip VTT/SRT timestamps and tags, return clean text."""
        lines = []
        seen = set()

        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
                continue
            if "-->" in line:
                if max_duration_sec is not None:
                    ts = line.split("-->")[0].strip()
                    secs = self._timestamp_to_sec(ts)
                    if secs is not None and secs > max_duration_sec:
                        break
                continue
            if re.match(r"^\d+$", line):
                continue

            clean = re.sub(r"<[^>]+>", "", line)
            clean = re.sub(r"\{[^}]+\}", "", clean)
            clean = clean.strip()

            if clean and clean not in seen:
                seen.add(clean)
                lines.append(clean)

        return " ".join(lines)

    def _timestamp_to_sec(self, ts: str) -> float | None:
        """Parse HH:MM:SS.mmm or MM:SS.mmm to seconds."""
        match = re.match(r"(?:(\d+):)?(\d+):(\d+)(?:[.,](\d+))?", ts)
        if not match:
            return None
        h = int(match.group(1) or 0)
        m = int(match.group(2))
        s = int(match.group(3))
        return h * 3600 + m * 60 + s
