"""Text translation via Claude (Anthropic SDK)."""

import asyncio
import logging

import anthropic

from app.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a professional translator. Translate the following text to {language}. "
    "Preserve the original meaning, tone, and structure. "
    "Output ONLY the translated text, nothing else."
)


class TranslatorService:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    async def translate(self, text: str, target_language: str) -> str:
        """Translate text to target language using Claude."""
        try:
            return await asyncio.to_thread(
                self._translate_sync, text, target_language
            )
        except ExternalServiceError:
            raise
        except Exception as err:
            raise ExternalServiceError(
                message=f"Translation failed: {err}",
                operation="translate",
            ) from err

    def _translate_sync(self, text: str, target_language: str) -> str:
        system = SYSTEM_PROMPT.format(language=target_language)
        response = self._client.messages.create(
            model=self._model,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": text}],
        )
        translated = response.content[0].text
        logger.info(
            "Translated %d chars → %d chars (%s)",
            len(text),
            len(translated),
            target_language,
        )
        return translated
