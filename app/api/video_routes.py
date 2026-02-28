"""Video analysis endpoint."""

from fastapi import APIRouter, Depends

from app.dependencies import get_youtube_service, get_cost_calculator
from app.models import AnalyzeRequest, AnalyzeResponse, VideoInfo
from app.services.youtube import YouTubeService
from app.services.cost_calculator import CostCalculator

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_video(
    body: AnalyzeRequest,
    youtube: YouTubeService = Depends(get_youtube_service),
    calculator: CostCalculator = Depends(get_cost_calculator),
):
    info = await youtube.get_video_info(str(body.url))
    video = VideoInfo(**info)
    tiers = calculator.calculate_tiers(video.duration_seconds)
    return AnalyzeResponse(video=video, tiers=tiers)
