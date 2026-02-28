# MasterPi AI — Pipeline Process

## Entrypoints

| Command | What it does |
|---------|-------------|
| `python run.py` | Start API server on `0.0.0.0:8000` |
| `python run.py --reload` | Start with auto-reload (development) |
| `python tools/cost_breakdown.py --url <youtube_url>` | CLI cost estimator |
| `python tools/cost_breakdown.py 3600` | Cost estimate for N seconds |

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | App status check |
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/languages` | List 29 supported languages |
| `POST` | `/api/v1/videos/analyze` | Analyze YouTube URL → video info + 3 tier costs |
| `POST` | `/api/v1/jobs` | Create audiobook job → starts pipeline |
| `GET` | `/api/v1/jobs/{id}` | Poll job status |
| `GET` | `/api/v1/jobs/{id}/stream` | SSE real-time progress stream |
| `GET` | `/api/v1/jobs/{id}/audio` | Download final MP3 |

---

## Pipeline Sequence

When a user creates a job via `POST /api/v1/jobs`, the pipeline runs as a background `asyncio.Task`. Each step updates the job status and pushes SSE events to connected clients.

```
POST /api/v1/jobs { url, tier, target_language }
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  STEP 1: DOWNLOAD AUDIO                             │
│  Status: downloading | Progress: 5%                 │
│  Service: YouTubeService                            │
│  File: app/services/youtube.py                      │
│                                                     │
│  - Fetch video metadata (title, duration, thumbnail)│
│  - Calculate tier duration from percentage fraction: │
│      SHORT  = 12.5% of full duration                │
│      MEDIUM = 40% of full duration                  │
│      FULL   = 100%                                  │
│  - Download audio via yt-dlp with --download-sections│
│    to limit duration per tier                       │
│  - Output: output/{job_id}/source.wav               │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  STEP 2: TRANSCRIBE SPEECH                          │
│  Status: transcribing | Progress: 20%               │
│  Service: TranscriberService                        │
│  File: app/services/transcriber.py                  │
│                                                     │
│  - Load faster-whisper model (lazy, first call only)│
│    Model: large-v3, Device: cpu, Compute: int8      │
│  - Transcribe WAV → plain text                      │
│  - Uses beam_size=5 for accuracy                    │
│  - Output: full transcript string                   │
│  - Cost: FREE (local inference)                     │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  STEP 3: EXTRACT VOICE SAMPLE                       │
│  Status: extracting_voice | Progress: 35%           │
│  Service: VoiceSampleExtractor                      │
│  File: app/services/voice_sample.py                 │
│                                                     │
│  - Extract first 45 seconds of audio via pydub      │
│  - Export as WAV for voice cloning input             │
│  - Output: output/{job_id}/voice_sample.wav         │
│  - Cost: FREE (local processing)                    │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  STEP 4: CLONE VOICE                                │
│  Status: cloning_voice | Progress: 45%              │
│  Service: VoiceClonerService                        │
│  File: app/services/voice_cloner.py                 │
│                                                     │
│  - POST voice_sample.wav to ElevenLabs /voices/add  │
│  - Uses httpx with xi-api-key header                │
│  - Returns voice_id for TTS step                    │
│  - Voice is deleted after job completes (cleanup)   │
│  - Output: ElevenLabs voice_id string               │
│  - Cost: included in ElevenLabs plan                │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  STEP 5: TRANSLATE TEXT                              │
│  Status: translating | Progress: 60%                │
│  Service: TranslatorService                         │
│  File: app/services/translator.py                   │
│                                                     │
│  - Split transcript into ~10,000 char chunks        │
│    at paragraph boundaries                          │
│  - Each chunk translated via LangChain chain:       │
│      ChatAnthropic (Claude Sonnet) + prompt template│
│  - First chunk: system prompt + text                │
│  - Continuation chunks: include 500 chars of        │
│    previous translation for terminology continuity  │
│  - System prompt enforces: preserve tone, keep      │
│    proper nouns, output ONLY translated text        │
│  - Output: full translated text string              │
│  - Cost: ~$0.022/min of audio                       │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  STEP 6: TEXT-TO-SPEECH                              │
│  Status: synthesizing | Progress: 75%               │
│  Service: TTSService                                │
│  File: app/services/tts.py                          │
│                                                     │
│  - Split translated text into ≤4500 char chunks     │
│    at sentence boundaries                           │
│  - Each chunk → POST to ElevenLabs                  │
│    /text-to-speech/{voice_id}                       │
│  - Uses cloned voice from Step 4                    │
│  - Model: eleven_multilingual_v2                    │
│  - Settings: stability=0.5, similarity_boost=0.75   │
│  - Output: output/{job_id}/tts_chunk_NNNN.mp3       │
│  - Cost: ~$0.10/min of audio                        │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  STEP 7: CONCATENATE AUDIO                          │
│  Status: concatenating | Progress: 90%              │
│  Service: AudioConcatService                        │
│  File: app/services/audio_concat.py                 │
│                                                     │
│  - Load all TTS MP3 chunks via pydub                │
│  - Concatenate in order                             │
│  - Export as single MP3 at 192kbps                  │
│  - Output: output/{job_id}/audiobook.mp3            │
│  - Cost: FREE (local processing)                    │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  STEP 8: COMPLETE                                   │
│  Status: completed | Progress: 100%                 │
│  Cleanup: DELETE cloned voice from ElevenLabs       │
│                                                     │
│  - Job marked as completed                          │
│  - Audio available at GET /api/v1/jobs/{id}/audio   │
│  - SSE stream sends final "completed" event         │
│  - Cloned voice deleted from ElevenLabs account     │
└─────────────────────────────────────────────────────┘
```

## SSE Event Format

Connected via `GET /api/v1/jobs/{id}/stream` (EventSource).

Each event:
```json
{
  "event": "progress",
  "data": {
    "status": "translating",
    "progress_pct": 60,
    "current_stage": "Translating text",
    "error": null
  }
}
```

Terminal events: `status: "completed"` or `status: "failed"` (with `error` message).

## Error Handling

- If any step fails, the job status is set to `failed` with the error message.
- The cloned voice is always cleaned up (even on failure) in the `finally` block.
- Each service wraps errors in domain exceptions (`PipelineError`, `ExternalServiceError`, `DownloadError`).
- The API returns structured error responses: `{ error, message, operation, entity_id }`.

## Cost Model

| Step | Cost/min | Source |
|------|----------|--------|
| Download | FREE | yt-dlp (local) |
| Transcribe | FREE | faster-whisper (local) |
| Voice sample | FREE | pydub (local) |
| Voice clone | FREE | ElevenLabs plan |
| Translate | $0.022 | Claude Sonnet API |
| TTS | $0.100 | ElevenLabs API |
| Concatenate | FREE | pydub (local) |

Plus: 25% platform margin + Stripe fee (2.9% + $0.30).

Tier pricing scales proportionally:
- **Short** = 12.5% of video → cost is ~1/8th of Full
- **Medium** = 40% of video → cost is ~1/2.5th of Full
- **Full** = 100% of video

## File Structure (per job)

```
output/{job_id}/
├── source.wav           # Downloaded audio (tier-limited)
├── voice_sample.wav     # 45s voice sample
├── tts_chunk_0000.mp3   # TTS output chunks
├── tts_chunk_0001.mp3
├── ...
└── audiobook.mp3        # Final concatenated audiobook
```

## Service Dependency Graph

```
PipelineOrchestrator
├── YouTubeService          (yt-dlp)
├── TranscriberService      (faster-whisper)
├── VoiceSampleExtractor    (pydub)
├── VoiceClonerService      (httpx → ElevenLabs API)
├── TranslatorService       (LangChain → Claude API)
├── TTSService              (httpx → ElevenLabs API)
├── AudioConcatService      (pydub)
├── CostCalculator          (pure math)
└── JobManager              (in-memory state + SSE queues)
```

All services are constructed in `app/dependencies.py` via `@lru_cache` factories and wired into the pipeline through FastAPI's `Depends()` system.
