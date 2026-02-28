"""Job CRUD, SSE streaming, and audio download endpoints."""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.dependencies import get_job_manager, get_pipeline
from app.languages import LANGUAGE_CODES
from app.models import CreateJobRequest, JobResponse, JobStatus
from app.services.job_manager import JobManager
from app.services.pipeline import PipelineOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(
    body: CreateJobRequest,
    jobs: JobManager = Depends(get_job_manager),
    pipeline: PipelineOrchestrator = Depends(get_pipeline),
):
    if body.target_language not in LANGUAGE_CODES:
        raise HTTPException(status_code=422, detail=f"Unsupported language: {body.target_language}")

    job_id = jobs.create_job(
        url=str(body.url),
        tier=body.tier.value,
        target_language=body.target_language,
    )

    asyncio.create_task(pipeline.run(job_id))

    job = jobs.get_job(job_id)
    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        progress_pct=job.progress_pct,
        current_stage=job.current_stage,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, jobs: JobManager = Depends(get_job_manager)):
    job = jobs.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        progress_pct=job.progress_pct,
        current_stage=job.current_stage,
        error=job.error,
    )


@router.get("/{job_id}/stream")
async def stream_job(job_id: str, jobs: JobManager = Depends(get_job_manager)):
    job = jobs.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    queue = jobs.subscribe(job_id)

    async def event_generator():
        try:
            while True:
                event = await asyncio.wait_for(queue.get(), timeout=300)
                yield {
                    "event": "progress",
                    "data": event.model_dump_json(),
                }
                if event.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                    break
        except asyncio.TimeoutError:
            yield {"event": "timeout", "data": "{}"}
        finally:
            jobs.unsubscribe(job_id, queue)

    return EventSourceResponse(event_generator())


@router.get("/{job_id}/audio")
async def download_audio(job_id: str, jobs: JobManager = Depends(get_job_manager)):
    job = jobs.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED or job.audio_path is None:
        raise HTTPException(status_code=404, detail="Audio not ready")

    def iter_file():
        with open(job.audio_path, "rb") as f:
            while chunk := f.read(65536):
                yield chunk

    return StreamingResponse(
        iter_file(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'attachment; filename="audiobook-{job_id}.mp3"',
        },
    )
