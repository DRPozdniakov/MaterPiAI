"""Language list endpoint."""

from fastapi import APIRouter

from app.languages import SUPPORTED_LANGUAGES
from app.models import LanguageResponse

router = APIRouter(prefix="/languages", tags=["languages"])


@router.get("", response_model=list[LanguageResponse])
async def list_languages():
    return SUPPORTED_LANGUAGES
