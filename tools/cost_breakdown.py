"""CLI tool to calculate audiobook cost breakdown.

Usage:
    python tools/cost_breakdown.py 3600          # 1 hour video (seconds)
    python tools/cost_breakdown.py 45:30         # 45 min 30 sec (mm:ss)
    python tools/cost_breakdown.py 1:30:00       # 1.5 hours (hh:mm:ss)
    python tools/cost_breakdown.py --url https://youtube.com/watch?v=...
"""

import argparse
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from app.models import TierCost
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


def fetch_video_info(url: str) -> tuple[int, str, str]:
    """Fetch video duration, title, channel from YouTube URL."""
    import yt_dlp

    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return (
            info.get("duration", 0),
            info.get("title", "Unknown"),
            info.get("channel", info.get("uploader", "Unknown")),
        )


def fmt(value: float) -> str:
    """Format USD value."""
    if value == 0:
        return "FREE"
    if value < 0.01:
        return f"${value:.4f}"
    return f"${value:.2f}"


def fmt_dur(minutes: float) -> str:
    """Format duration nicely."""
    if minutes >= 60:
        h = int(minutes // 60)
        m = int(minutes % 60)
        return f"{h}h {m}m"
    return f"{minutes:.0f}m"


def print_header(title: str, channel: str, duration_sec: int) -> None:
    w = 62
    print("+" + "-" * w + "+")
    print(f"|{'MASTERPI AI - COST BREAKDOWN':^{w}}|")
    print("+" + "-" * w + "+")
    print(f"|  Video:    {title[:w-13]:<{w-13}} |")
    print(f"|  Channel:  {channel[:w-13]:<{w-13}} |")
    h, m, s = duration_sec // 3600, (duration_sec % 3600) // 60, duration_sec % 60
    dur_str = f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s"
    print(f"|  Duration: {dur_str:<{w-13}} |")
    print("+" + "-" * w + "+")


def print_pipeline_rates() -> None:
    w = 62
    print(f"|{'PIPELINE COST RATES (per minute)':^{w}}|")
    print("+" + "-" * w + "+")
    steps = [
        ("1. Download (yt-dlp)", "FREE", "local"),
        ("2. Transcribe (faster-whisper)", fmt(settings.cost_per_min_whisper), "local GPU/CPU"),
        ("3. Voice sample extraction", "FREE", "local pydub"),
        ("4. Voice clone (ElevenLabs)", fmt(settings.cost_per_min_voice_clone), "one-time per job"),
        ("5. Translate (Claude Sonnet)", fmt(settings.cost_per_min_translation), "~1k tokens/min"),
        ("6. TTS (ElevenLabs)", fmt(settings.cost_per_min_tts), "~1k chars/min"),
        ("7. Concat (pydub)", "FREE", "local"),
    ]
    for step, cost, note in steps:
        line = f"  {step:<32} {cost:>8}  {note}"
        print(f"|{line:<{w}}|")
    margin_line = f"  Platform margin: {settings.platform_margin * 100:.0f}%"
    stripe_line = f"  Stripe fee: {settings.stripe_fee_pct * 100:.1f}% + ${settings.stripe_fee_fixed:.2f}"
    print(f"|{'':<{w}}|")
    print(f"|{margin_line:<{w}}|")
    print(f"|{stripe_line:<{w}}|")
    print("+" + "-" * w + "+")


def print_tier_comparison(tiers: list[TierCost]) -> None:
    w = 62
    # Header row
    print(f"|{'TIER COMPARISON':^{w}}|")
    print("+" + "-" * 20 + "+" + "-" * 13 + "+" + "-" * 13 + "+" + "-" * 13 + "+")
    print(f"|{'':^20}|{'SHORT':^13}|{'MEDIUM':^13}|{'FULL':^13}|")
    print("+" + "-" * 20 + "+" + "-" * 13 + "+" + "-" * 13 + "+" + "-" * 13 + "+")

    short, medium, full = tiers[0], tiers[1], tiers[2]

    # Duration row
    row = f"|{'Duration':<20}|{fmt_dur(short.duration_minutes):^13}|{fmt_dur(medium.duration_minutes):^13}|{fmt_dur(full.duration_minutes):^13}|"
    print(row)

    # % of video
    short_pct = f"{settings.tier_short_fraction * 100:.0f}%"
    medium_pct = f"{settings.tier_medium_fraction * 100:.0f}%"
    row = f"|{'% of video':<20}|{short_pct:^13}|{medium_pct:^13}|{'100%':^13}|"
    print(row)

    print("+" + "-" * 20 + "+" + "-" * 13 + "+" + "-" * 13 + "+" + "-" * 13 + "+")

    # Cost rows
    rows = [
        ("Transcription", "transcription_cost"),
        ("Translation", "translation_cost"),
        ("TTS", "tts_cost"),
    ]
    for label, attr in rows:
        s = fmt(getattr(short, attr))
        m = fmt(getattr(medium, attr))
        f = fmt(getattr(full, attr))
        print(f"|{label:<20}|{s:^13}|{m:^13}|{f:^13}|")

    print("+" + "-" * 20 + "+" + "-" * 13 + "+" + "-" * 13 + "+" + "-" * 13 + "+")

    # Subtotals
    def subtotal(t: TierCost) -> float:
        return t.transcription_cost + t.translation_cost + t.tts_cost

    ss, sm, sf = fmt(subtotal(short)), fmt(subtotal(medium)), fmt(subtotal(full))
    print(f"|{'Subtotal':<20}|{ss:^13}|{sm:^13}|{sf:^13}|")

    # Margin
    def margin_amt(t: TierCost) -> float:
        return subtotal(t) * settings.platform_margin

    ms = fmt(margin_amt(short))
    mm = fmt(margin_amt(medium))
    mf = fmt(margin_amt(full))
    margin_label = f"Margin ({settings.platform_margin * 100:.0f}%)"
    print(f"|{margin_label:<20}|{ms:^13}|{mm:^13}|{mf:^13}|")

    # Stripe fee
    stripe_s = fmt(short.stripe_fee)
    stripe_m = fmt(medium.stripe_fee)
    stripe_f = fmt(full.stripe_fee)
    stripe_label = f"Stripe ({settings.stripe_fee_pct * 100:.1f}%+$0.30)"
    print(f"|{stripe_label:<20}|{stripe_s:^13}|{stripe_m:^13}|{stripe_f:^13}|")

    print("+" + "=" * 20 + "+" + "=" * 13 + "+" + "=" * 13 + "+" + "=" * 13 + "+")

    # Total
    ts, tm, tf = fmt(short.total_cost), fmt(medium.total_cost), fmt(full.total_cost)
    print(f"|{'TOTAL':<20}|{ts:^13}|{tm:^13}|{tf:^13}|")
    print("+" + "=" * 20 + "+" + "=" * 13 + "+" + "=" * 13 + "+" + "=" * 13 + "+")

    # Cost per minute
    cpm_s = f"${short.total_cost / short.duration_minutes:.3f}" if short.duration_minutes else "-"
    cpm_m = f"${medium.total_cost / medium.duration_minutes:.3f}" if medium.duration_minutes else "-"
    cpm_f = f"${full.total_cost / full.duration_minutes:.3f}" if full.duration_minutes else "-"
    print(f"|{'Cost/min':<20}|{cpm_s:^13}|{cpm_m:^13}|{cpm_f:^13}|")

    # Ratio vs full
    ratio_s = f"1/{full.total_cost / short.total_cost:.1f}" if short.total_cost else "-"
    ratio_m = f"1/{full.total_cost / medium.total_cost:.1f}" if medium.total_cost else "-"
    print(f"|{'vs Full':<20}|{ratio_s:^13}|{ratio_m:^13}|{'1x':^13}|")
    print("+" + "-" * 20 + "+" + "-" * 13 + "+" + "-" * 13 + "+" + "-" * 13 + "+")


def main():
    parser = argparse.ArgumentParser(description="Calculate audiobook cost breakdown")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("duration", nargs="?", help="Duration in seconds, mm:ss, or hh:mm:ss")
    group.add_argument("--url", help="YouTube URL to fetch duration from")

    parser.add_argument("--tts-rate", type=float, help="Override TTS cost/min")
    parser.add_argument("--translation-rate", type=float, help="Override translation cost/min")
    parser.add_argument("--margin", type=float, help="Override platform margin (0.0-1.0)")

    args = parser.parse_args()

    title, channel = "Manual input", "-"
    if args.url:
        duration_sec, title, channel = fetch_video_info(args.url)
    else:
        duration_sec = parse_duration(args.duration)

    calc = CostCalculator(
        cost_per_min_whisper=settings.cost_per_min_whisper,
        cost_per_min_translation=args.translation_rate or settings.cost_per_min_translation,
        cost_per_min_tts=args.tts_rate or settings.cost_per_min_tts,
        cost_per_min_voice_clone=settings.cost_per_min_voice_clone,
        platform_margin=args.margin if args.margin is not None else settings.platform_margin,
        tier_short_fraction=settings.tier_short_fraction,
        tier_medium_fraction=settings.tier_medium_fraction,
        stripe_fee_pct=settings.stripe_fee_pct,
        stripe_fee_fixed=settings.stripe_fee_fixed,
    )

    tiers = calc.calculate_tiers(duration_sec)

    print()
    print_header(title, channel, duration_sec)
    print_pipeline_rates()
    print_tier_comparison(tiers)
    print()


if __name__ == "__main__":
    main()
