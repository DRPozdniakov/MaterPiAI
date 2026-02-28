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

# Each stage: (start_pct, end_pct, label)
STAGES = [
    (JobStatus.DOWNLOADING,      0,  15, "Downloading audio"),
    (JobStatus.TRANSCRIBING,    15,  30, "Transcribing speech"),
    (JobStatus.EXTRACTING_VOICE,30,  38, "Extracting voice sample"),
    (JobStatus.CLONING_VOICE,   38,  48, "Cloning voice"),
    (JobStatus.TRANSLATING,     48,  65, "Translating text"),
    (JobStatus.SYNTHESIZING,    65,  90, "Synthesizing speech"),
    (JobStatus.CONCATENATING,   90,  98, "Building audiobook"),
]


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
        demo_max_seconds: int = 0,
        default_voice_id: str = "",
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
        self._demo_max = demo_max_seconds
        self._default_voice_id = default_voice_id

    async def run(self, job_id: str) -> None:
        """Execute the full audiobook pipeline for a job."""
        job = self._jobs.get_job(job_id)
        if job is None:
            return

        tier = Tier(job.tier)
        job_dir = self._output_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Download audio
            self._stage_start(job_id, JobStatus.DOWNLOADING)
            info = await self._youtube.get_video_info(job.url)

            if self._demo_max > 0:
                max_sec = self._demo_max
                logger.info("Demo mode: capping download to %ds", max_sec)
            else:
                max_sec = self._cost_calculator.tier_duration_seconds(
                    tier, info["duration_seconds"]
                )

            self._stage_mid(job_id, JobStatus.DOWNLOADING)
            audio_path = await self._youtube.download_audio(
                job.url, job_id, tier, max_sec
            )
            self._stage_end(job_id, JobStatus.DOWNLOADING)

            # 2. Transcribe (YouTube subtitles, with cache fallback)
            self._stage_start(job_id, JobStatus.TRANSCRIBING)
            cache_file = job_dir / "transcript.txt"
            if cache_file.exists():
                transcript = cache_file.read_text(encoding="utf-8")
                logger.info("Using cached transcript: %d chars", len(transcript))
            else:
                try:
                    transcript = await self._transcriber.transcribe(job.url, max_sec)
                    cache_file.write_text(transcript, encoding="utf-8")
                except Exception as tr_err:
                    logger.warning("Transcription failed, using fallback: %s", tr_err)
                    transcript = "This is a demo audiobook. The original transcript could not be fetched due to rate limiting. Please try again in a few minutes."
            self._stage_end(job_id, JobStatus.TRANSCRIBING)
            logger.info("Transcript: %d chars", len(transcript))

            # 3. Extract voice sample
            self._stage_start(job_id, JobStatus.EXTRACTING_VOICE)
            sample_path = await self._voice_sample.extract(audio_path, job_dir)
            self._stage_end(job_id, JobStatus.EXTRACTING_VOICE)

            # 4. Clone voice (fall back to default if cloning unavailable)
            self._stage_start(job_id, JobStatus.CLONING_VOICE)
            try:
                voice_id = await self._voice_cloner.clone_voice(
                    sample_path, f"masterpi-{job_id}"
                )
                job.voice_id = voice_id
            except Exception as clone_err:
                logger.warning("Voice cloning failed, using default voice: %s", clone_err)
                voice_id = self._default_voice_id
            self._stage_end(job_id, JobStatus.CLONING_VOICE)

            # 5. Translate
            self._stage_start(job_id, JobStatus.TRANSLATING)
            translated = await self._translator.translate(
                transcript, job.target_language
            )
            self._stage_end(job_id, JobStatus.TRANSLATING)
            logger.info("Translation: %d chars", len(translated))

            # 6. TTS — report progress per chunk
            self._stage_start(job_id, JobStatus.SYNTHESIZING)
            chunks = await self._tts.synthesize(
                translated, voice_id, job_dir,
                progress_cb=lambda done, total: self._sub_progress(
                    job_id, JobStatus.SYNTHESIZING, done, total
                ),
            )
            self._stage_end(job_id, JobStatus.SYNTHESIZING)

            # 7. Concatenate
            self._stage_start(job_id, JobStatus.CONCATENATING)
            final_path = job_dir / "audiobook.mp3"
            await self._audio_concat.concat(chunks, final_path)
            job.audio_path = final_path
            self._stage_end(job_id, JobStatus.CONCATENATING)

            # Done
            self._jobs.update_job(job_id, JobStatus.COMPLETED, 100, "Complete")
            logger.info("Job %s completed: %s", job_id, final_path)

        except Exception as err:
            logger.exception("Job %s failed", job_id)
            self._jobs.update_job(
                job_id, JobStatus.FAILED, 0, "Failed", str(err)
            )
        finally:
            if job.voice_id:
                await self._voice_cloner.delete_voice(job.voice_id)

    def _get_stage(self, status: JobStatus) -> tuple[int, int, str]:
        for s_status, s_start, s_end, s_label in STAGES:
            if s_status == status:
                return s_start, s_end, s_label
        return 0, 0, ""

    def _stage_start(self, job_id: str, status: JobStatus) -> None:
        start, _, label = self._get_stage(status)
        self._jobs.update_job(job_id, status, start, label)

    def _stage_mid(self, job_id: str, status: JobStatus) -> None:
        start, end, label = self._get_stage(status)
        mid = (start + end) // 2
        self._jobs.update_job(job_id, status, mid, label)

    def _stage_end(self, job_id: str, status: JobStatus) -> None:
        _, end, label = self._get_stage(status)
        self._jobs.update_job(job_id, status, end, label)

    def _sub_progress(self, job_id: str, status: JobStatus, done: int, total: int) -> None:
        """Report sub-step progress within a stage (e.g. TTS chunk 3/10)."""
        start, end, label = self._get_stage(status)
        if total > 0:
            frac = done / total
            pct = int(start + (end - start) * frac)
            self._jobs.update_job(job_id, status, pct, f"{label} ({done}/{total})")
