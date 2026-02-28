"""CLI tool to calculate audiobook cost breakdown.

Usage:
    python tools/cost_breakdown.py 3600          # 1 hour video (seconds)
    python tools/cost_breakdown.py 45:30         # 45 min 30 sec (mm:ss)
    python tools/cost_breakdown.py 1:30:00       # 1.5 hours (hh:mm:ss)
    python tools/cost_breakdown.py --url https://youtube.com/watch?v=...
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from app.models import Tier, TierCost
from app.services.cost_calculator import CostCalculator


def parse_duration(value: str) -> int:
    """Parse duration string to seconds. Accepts seconds, mm:ss, or hh:mm:ss."""
    parts = value.split(":")
    if len(parts) == 1:
        return int(parts[0])
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    raise ValueError(f"Invalid duration format: {value}")


def fetch_duration_from_url(url: str) -> int:
    """Fetch video duration from YouTube URL using yt-dlp."""
    import yt_dlp

    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        duration = info.get("duration", 0)
        title = info.get("title", "Unknown")
        print(f"Video: {title}")
        print(f"Duration: {duration // 3600}h {(duration % 3600) // 60}m {duration % 60}s")
        print()
        return duration


def format_usd(value: float) -> str:
    return f"${value:.4f}" if value < 0.01 else f"${value:.2f}"


def print_breakdown(tiers: list[TierCost], duration_sec: int) -> None:
    print(f"Video duration: {duration_sec // 60}m {duration_sec % 60}s ({duration_sec}s)")
    print(f"Tier caps: Short={settings.tier_short_min}min, Medium={settings.tier_medium_min}min, Full=entire")
    print()

    # Rate card
    print("=== Rate Card (per minute) ===")
    print(f"  Transcription (faster-whisper): {format_usd(settings.cost_per_min_whisper)}")
    print(f"  Translation (Claude Sonnet):    {format_usd(settings.cost_per_min_translation)}")
    print(f"  TTS (ElevenLabs):               {format_usd(settings.cost_per_min_tts)}")
    print(f"  Voice clone:                    {format_usd(settings.cost_per_min_voice_clone)}")
    print(f"  Platform margin:                {settings.platform_margin * 100:.0f}%")
    print()

    # Per-tier breakdown
    for tier_cost in tiers:
        label = tier_cost.tier.value.upper()
        print(f"=== {label} TIER ({tier_cost.duration_minutes} min) ===")
        print(f"  Transcription:  {format_usd(tier_cost.transcription_cost)}")
        print(f"  Translation:    {format_usd(tier_cost.translation_cost)}")
        print(f"  TTS:            {format_usd(tier_cost.tts_cost)}")
        subtotal = tier_cost.transcription_cost + tier_cost.translation_cost + tier_cost.tts_cost
        print(f"  Subtotal:       {format_usd(subtotal)}")
        print(f"  + Margin (25%): {format_usd(tier_cost.total_cost - subtotal)}")
        print(f"  ---------------------")
        print(f"  TOTAL:          {format_usd(tier_cost.total_cost)}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Calculate audiobook cost breakdown")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("duration", nargs="?", help="Duration in seconds, mm:ss, or hh:mm:ss")
    group.add_argument("--url", help="YouTube URL to fetch duration from")

    # Override rates
    parser.add_argument("--tts-rate", type=float, help="Override TTS cost/min")
    parser.add_argument("--translation-rate", type=float, help="Override translation cost/min")
    parser.add_argument("--margin", type=float, help="Override platform margin (0.0-1.0)")

    args = parser.parse_args()

    if args.url:
        duration_sec = fetch_duration_from_url(args.url)
    else:
        duration_sec = parse_duration(args.duration)

    calc = CostCalculator(
        cost_per_min_whisper=settings.cost_per_min_whisper,
        cost_per_min_translation=args.translation_rate or settings.cost_per_min_translation,
        cost_per_min_tts=args.tts_rate or settings.cost_per_min_tts,
        cost_per_min_voice_clone=settings.cost_per_min_voice_clone,
        platform_margin=args.margin if args.margin is not None else settings.platform_margin,
        tier_short_min=settings.tier_short_min,
        tier_medium_min=settings.tier_medium_min,
    )

    tiers = calc.calculate_tiers(duration_sec)
    print_breakdown(tiers, duration_sec)


if __name__ == "__main__":
    main()
