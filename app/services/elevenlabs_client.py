"""ElevenLabs async client factory with Protocol-based interface."""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from elevenlabs import AsyncElevenLabs

from config.settings import settings

logger = logging.getLogger(__name__)


@runtime_checkable
class ElevenLabsClientProvider(Protocol):
    """Protocol so services can accept any client factory (real or mock)."""

    def get_client(self, api_key: str | None = None) -> AsyncElevenLabs: ...


class ElevenLabsClientFactory:
    """Creates AsyncElevenLabs clients.

    Per-request API key takes priority; env-configured key is fallback.
    Each call returns a fresh client (cheap httpx wrapper) because API keys
    can differ per request.
    """

    def get_client(self, api_key: str | None = None) -> AsyncElevenLabs:
        key = api_key or settings.elevenlabs.api_key
        if not key:
            raise ValueError(
                "No ElevenLabs API key provided. Pass api_key or set it in config."
            )
        return AsyncElevenLabs(api_key=key)
