"""Text translation via LangChain + Claude with chunked processing."""

import logging
import re

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from app.exceptions import ExternalServiceError, ValidationError
from app.languages import LANGUAGE_CODES

logger = logging.getLogger(__name__)

SYSTEM_TEMPLATE = (
    "You are a professional audiobook translator.\n"
    "Target language: {language}\n\n"
    "Rules:\n"
    "- Preserve the original meaning, tone, and narrative structure\n"
    "- Keep proper nouns, names, and technical terms consistent\n"
    "- Maintain paragraph breaks\n"
    "- Output ONLY the translated text, nothing else\n"
    "- Do NOT add explanations, notes, or commentary"
)

FIRST_CHUNK_HUMAN = "Translate the following text:\n\n{text}"

CONTINUATION_HUMAN = (
    "For continuity, here is the end of the previously translated section:\n"
    "---\n{context}\n---\n\n"
    "Now translate the next section (do NOT re-translate the context above):\n\n{text}"
)

CHUNK_MAX_CHARS = 10_000
CONTEXT_OVERLAP_CHARS = 500


class TranslatorService:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._llm = ChatAnthropic(
            model_name=model,
            api_key=api_key,
            max_tokens_to_sample=16000,
            temperature=0.3,
        )
        self._first_chain = self._build_first_chain()
        self._continuation_chain = self._build_continuation_chain()

    def _build_first_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE),
            HumanMessagePromptTemplate.from_template(FIRST_CHUNK_HUMAN),
        ])
        return prompt | self._llm

    def _build_continuation_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE),
            HumanMessagePromptTemplate.from_template(CONTINUATION_HUMAN),
        ])
        return prompt | self._llm

    async def translate(self, text: str, target_language: str) -> str:
        """Translate text in chunks for quality. Returns full translated text."""
        if target_language not in LANGUAGE_CODES:
            raise ValidationError(
                message=f"Unsupported language: {target_language}",
                operation="translate",
            )
        chunks = self._split_into_chunks(text)
        logger.info(
            "Translation: %d chars -> %d chunks (%s)",
            len(text), len(chunks), target_language,
        )

        translated_parts = []
        prev_translated_tail = ""

        for i, chunk in enumerate(chunks):
            logger.info("Translating chunk %d/%d (%d chars)", i + 1, len(chunks), len(chunk))
            try:
                translated = await self._translate_chunk(
                    chunk, target_language, prev_translated_tail
                )
                translated_parts.append(translated)
                prev_translated_tail = translated[-CONTEXT_OVERLAP_CHARS:]
            except ExternalServiceError:
                raise
            except Exception as err:
                raise ExternalServiceError(
                    message=f"Translation chunk {i+1}/{len(chunks)} failed: {err}",
                    operation="translate",
                ) from err

        full_translation = "\n\n".join(translated_parts)
        logger.info(
            "Translation complete: %d chars -> %d chars (%s)",
            len(text), len(full_translation), target_language,
        )
        return full_translation

    def _split_into_chunks(self, text: str) -> list[str]:
        """Split text into chunks at paragraph boundaries."""
        if len(text) <= CHUNK_MAX_CHARS:
            return [text]

        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current = ""

        for para in paragraphs:
            if len(current) + len(para) + 2 > CHUNK_MAX_CHARS and current:
                chunks.append(current.strip())
                current = para
            else:
                current = f"{current}\n\n{para}" if current else para

        if current.strip():
            chunks.append(current.strip())

        return chunks if chunks else [text]

    async def _translate_chunk(
        self, text: str, target_language: str, prev_context: str
    ) -> str:
        if prev_context:
            result = await self._continuation_chain.ainvoke({
                "language": target_language,
                "context": prev_context,
                "text": text,
            })
        else:
            result = await self._first_chain.ainvoke({
                "language": target_language,
                "text": text,
            })
        content = result.content
        if isinstance(content, str):
            return content
        return "".join(
            block if isinstance(block, str) else str(block)
            for block in content
        )
