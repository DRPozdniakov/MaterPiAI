"""Per-tier cost estimation."""

import logging

from app.models import Tier, TierCost

logger = logging.getLogger(__name__)


class CostCalculator:
    def __init__(
        self,
        cost_per_min_whisper: float,
        cost_per_min_translation: float,
        cost_per_min_tts: float,
        cost_per_min_voice_clone: float,
        platform_margin: float,
        tier_short_fraction: float,
        tier_medium_fraction: float,
    ):
        self._rates = {
            "whisper": cost_per_min_whisper,
            "translation": cost_per_min_translation,
            "tts": cost_per_min_tts,
            "voice_clone": cost_per_min_voice_clone,
        }
        self._margin = platform_margin
        self._short_frac = tier_short_fraction
        self._medium_frac = tier_medium_fraction

    def calculate_tiers(self, duration_seconds: int) -> list[TierCost]:
        full_min = duration_seconds / 60.0
        tiers = []
        for tier in Tier:
            minutes = self._tier_duration(tier, full_min)
            tiers.append(self._build_tier_cost(tier, minutes))
        return tiers

    def tier_duration_seconds(self, tier: Tier, total_duration_sec: int) -> int | None:
        """Return max seconds for tier, or None for full."""
        if tier == Tier.SHORT:
            return int(total_duration_sec * self._short_frac)
        if tier == Tier.MEDIUM:
            return int(total_duration_sec * self._medium_frac)
        return None

    def _tier_duration(self, tier: Tier, full_min: float) -> float:
        if tier == Tier.SHORT:
            return round(full_min * self._short_frac, 1)
        if tier == Tier.MEDIUM:
            return round(full_min * self._medium_frac, 1)
        return full_min

    def _build_tier_cost(self, tier: Tier, minutes: float) -> TierCost:
        transcription = round(minutes * self._rates["whisper"], 4)
        translation = round(minutes * self._rates["translation"], 4)
        tts = round(minutes * self._rates["tts"], 4)
        subtotal = transcription + translation + tts
        total = round(subtotal * (1 + self._margin), 2)
        return TierCost(
            tier=tier,
            duration_minutes=round(minutes, 1),
            transcription_cost=transcription,
            translation_cost=translation,
            tts_cost=tts,
            total_cost=total,
        )
