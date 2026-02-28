"""Pipeline orchestrator — wires all services for audiobook generation."""

import logging
from pathlib import Path

from app.models import JobStatus, Tier
from app.services.audio_concat import AudioConcatService
from app.services.cost_calculator import CostCalculator
from app.services.job_manager import JobManager
from app.services.transcriber import TranscriberService
from app.services.translator import TranslatorService
from app.services.tts import TTSService
from app.services.voice_cloner import VoiceClonerService
from app.services.voice_sample import VoiceSampleExtractor
from app.services.youtube import YouTubeService

logger = logging.getLogger(__name__)

STAGE_PROGRESS = {
    JobStatus.DOWNLOADING: (5, "Downloading audio"),
    JobStatus.TRANSCRIBING: (20, "Transcribing speech"),
    JobStatus.EXTRACTING_VOICE: (35, "Extracting voice sample"),
    JobStatus.CLONING_VOICE: (45, "Cloning voice"),
    JobStatus.TRANSLATING: (60, "Translating text"),
    JobStatus.SYNTHESIZING: (75, "Synthesizing speech"),
    JobStatus.CONCATENATING: (90, "Building audiobook"),
    JobStatus.COMPLETED: (100, "Complete"),
}


class PipelineOrchestrator:
    def __init__(
        self,
        youtube: YouTubeService,
        transcriber: TranscriberService,
        voice_sample: VoiceSampleExtractor,
        voice_cloner: VoiceClonerService,
        translator: TranslatorService,
        tts: TTSService,
        audio_concat: AudioConcatService,
        cost_calculator: CostCalculator,
        job_manager: JobManager,
        output_dir: str,
    ):
        self._youtube = youtube
        self._transcriber = transcriber
        self._voice_sample = voice_sample
        self._voice_cloner = voice_cloner
        self._translator = translator
        self._tts = tts
        self._audio_concat = audio_concat
        self._cost_calculator = cost_calculator
        self._jobs = job_manager
        self._output_dir = Path(output_dir)

    async def run(self, job_id: str) -> None:
        """Execute the full audiobook pipeline for a job."""
        job = self._jobs.get_job(job_id)
        if job is None:
            return

        tier = Tier(job.tier)
        job_dir = self._output_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Get video info for tier duration
            self._update(job_id, JobStatus.DOWNLOADING)
            info = await self._youtube.get_video_info(job.url)
            max_sec = self._cost_calculator.tier_duration_seconds(
                tier, info["duration_seconds"]
            )
            audio_path = await self._youtube.download_audio(
                job.url, job_id, tier, max_sec
            )

            # 2. Transcribe
            self._update(job_id, JobStatus.TRANSCRIBING)
            transcript = await self._transcriber.transcribe(audio_path)

            # 3. Extract voice sample
            self._update(job_id, JobStatus.EXTRACTING_VOICE)
            sample_path = await self._voice_sample.extract(audio_path, job_dir)

            # 4. Clone voice
            self._update(job_id, JobStatus.CLONING_VOICE)
            voice_id = await self._voice_cloner.clone_voice(
                sample_path, f"masterpi-{job_id}"
            )
            job.voice_id = voice_id

            # 5. Translate
            self._update(job_id, JobStatus.TRANSLATING)
            translated = await self._translator.translate(
                transcript, job.target_language
            )

            # 6. TTS
            self._update(job_id, JobStatus.SYNTHESIZING)
            chunks = await self._tts.synthesize(translated, voice_id, job_dir)

            # 7. Concatenate
            self._update(job_id, JobStatus.CONCATENATING)
            final_path = job_dir / "audiobook.mp3"
            await self._audio_concat.concat(chunks, final_path)
            job.audio_path = final_path

            # Done
            self._update(job_id, JobStatus.COMPLETED)
            logger.info("Job %s completed: %s", job_id, final_path)

        except Exception as err:
            logger.exception("Job %s failed", job_id)
            self._jobs.update_job(
                job_id, JobStatus.FAILED, 0, "Failed", str(err)
            )
        finally:
            # Cleanup cloned voice
            if job.voice_id:
                await self._voice_cloner.delete_voice(job.voice_id)

    def _update(self, job_id: str, status: JobStatus) -> None:
        pct, stage = STAGE_PROGRESS[status]
        self._jobs.update_job(job_id, status, pct, stage)
