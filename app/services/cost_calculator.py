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
        tier_short_min: int,
        tier_medium_min: int,
    ):
        self._rates = {
            "whisper": cost_per_min_whisper,
            "translation": cost_per_min_translation,
            "tts": cost_per_min_tts,
            "voice_clone": cost_per_min_voice_clone,
        }
        self._margin = platform_margin
        self._tier_short = tier_short_min
        self._tier_medium = tier_medium_min

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
            return min(self._tier_short * 60, total_duration_sec)
        if tier == Tier.MEDIUM:
            return min(self._tier_medium * 60, total_duration_sec)
        return None

    def _tier_duration(self, tier: Tier, full_min: float) -> float:
        if tier == Tier.SHORT:
            return min(self._tier_short, full_min)
        if tier == Tier.MEDIUM:
            return min(self._tier_medium, full_min)
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
