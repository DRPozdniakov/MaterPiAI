"""YouTube video metadata and audio download via yt-dlp."""

import asyncio
import logging
from pathlib import Path

from app.exceptions import DownloadError
from app.models import Tier

logger = logging.getLogger(__name__)


class YouTubeService:
    def __init__(self, output_dir: str):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    async def get_video_info(self, url: str) -> dict:
        """Fetch video metadata without downloading."""
        try:
            info = await asyncio.to_thread(self._extract_info, url)
            return {
                "title": info.get("title", "Unknown"),
                "channel": info.get("channel", info.get("uploader", "Unknown")),
                "duration_seconds": info.get("duration", 0),
                "thumbnail_url": info.get("thumbnail", ""),
            }
        except Exception as err:
            raise DownloadError(
                message=f"Failed to fetch video info: {err}",
                operation="get_video_info",
                entity_id=url,
            ) from err

    async def download_audio(
        self, url: str, job_id: str, tier: Tier, max_duration_sec: int | None = None
    ) -> Path:
        """Download audio as WAV. Optionally limit duration via --download-sections."""
        output_path = self._output_dir / job_id / "source.wav"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            await asyncio.to_thread(
                self._download, url, str(output_path), max_duration_sec
            )
            return output_path
        except Exception as err:
            raise DownloadError(
                message=f"Failed to download audio: {err}",
                operation="download_audio",
                entity_id=job_id,
            ) from err

    def _extract_info(self, url: str) -> dict:
        import yt_dlp

        opts = {"quiet": True, "no_warnings": True, "skip_download": True, "cookiesfrombrowser": ("chrome",)}
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _download(
        self, url: str, output_path: str, max_duration_sec: int | None
    ) -> None:
        import yt_dlp

        opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path.replace(".wav", ".%(ext)s"),
                        "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "0",
                }
            ],
            "quiet": True,
            "no_warnings": True,
        }
        if max_duration_sec is not None:
            opts["download_ranges"] = yt_dlp.utils.download_range_func(
                None, [(0, max_duration_sec)]
            )
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
