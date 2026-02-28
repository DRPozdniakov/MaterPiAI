"""In-memory job state management with SSE subscriber queues."""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.models import JobStatus, SSEEvent

logger = logging.getLogger(__name__)


@dataclass
class Job:
    job_id: str
    url: str
    tier: str
    target_language: str
    status: JobStatus = JobStatus.PENDING
    progress_pct: int = 0
    current_stage: str = "Waiting"
    error: str | None = None
    audio_path: Path | None = None
    voice_id: str | None = None
    subscribers: list[asyncio.Queue] = field(default_factory=list)


class JobManager:
    def __init__(self):
        self._jobs: dict[str, Job] = {}

    def create_job(self, url: str, tier: str, target_language: str) -> str:
        job_id = uuid.uuid4().hex[:12]
        self._jobs[job_id] = Job(
            job_id=job_id,
            url=url,
            tier=tier,
            target_language=target_language,
        )
        logger.info("Job created: %s", job_id)
        return job_id

    def get_job(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def update_job(
        self,
        job_id: str,
        status: JobStatus,
        progress_pct: int,
        stage: str,
        error: str | None = None,
    ) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            return
        job.status = status
        job.progress_pct = progress_pct
        job.current_stage = stage
        job.error = error

        event = SSEEvent(
            status=status,
            progress_pct=progress_pct,
            current_stage=stage,
            error=error,
        )
        for queue in job.subscribers:
            queue.put_nowait(event)

    def subscribe(self, job_id: str) -> asyncio.Queue | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        queue: asyncio.Queue = asyncio.Queue()
        job.subscribers.append(queue)
        return queue

    def unsubscribe(self, job_id: str, queue: asyncio.Queue) -> None:
        job = self._jobs.get(job_id)
        if job and queue in job.subscribers:
            job.subscribers.remove(queue)
