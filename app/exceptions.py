"""Custom exception hierarchy for MasterPi AI."""


class MasterPiAIException(Exception):
    """Base exception for all MasterPi AI errors."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        entity_id: str | None = None,
        details: dict | None = None,
    ):
        self.message = message
        self.operation = operation
        self.entity_id = entity_id
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(MasterPiAIException):
    """Database operation failures."""


class LLMError(MasterPiAIException):
    """LLM provider failures."""


class PipelineError(MasterPiAIException):
    """Processing pipeline failures."""


class ValidationError(MasterPiAIException):
    """Input validation failures."""


class ExternalServiceError(MasterPiAIException):
    """External API call failures (ElevenLabs, Anthropic, etc.)."""


class ElevenLabsError(ExternalServiceError):
    """ElevenLabs API failures."""


class DownloadError(MasterPiAIException):
    """YouTube / media download failures."""
