# YouTube Audiobook Translator — Implementation Plan

## Context
Build a web app that takes a YouTube audiobook/spoken content URL, clones the speaker's voice via ElevenLabs, translates the transcript to any language, and generates a translated audiobook in the original speaker's voice. All speech-based — fully within ElevenLabs' capabilities.

## Pipeline
```
YouTube URL → yt-dlp (download) → Demucs (optional vocal cleanup)
  → faster-whisper (transcribe) → extract 45s voice sample
  → ElevenLabs Instant Voice Clone → Claude API (translate)
  → ElevenLabs TTS with cloned voice (request stitching) → final MP3
```

## Tech Stack
| Component | Choice | Why |
|---|---|---|
| Backend | **FastAPI** | Native async, SSE support, auto-docs |
| Frontend | **Plain HTML/CSS/JS** | No build step, fast for hackathon |
| Progress | **SSE (Server-Sent Events)** | Simpler than WebSockets, sufficient |
| Transcription | **faster-whisper** (base model) | 4x faster than OpenAI Whisper, same accuracy |
| TTS | **ElevenLabs eleven_multilingual_v2** | 29 languages, request stitching for seamless chunks |
| Translation | **Claude Sonnet** via Anthropic API | Quality literary translation |
| Audio | **pydub + ffmpeg** | Concatenation, format conversion |

## Project Structure
```
UCL/
├── requirements.txt
├── .env.example
├── .gitignore
├── app/
│   ├── main.py                  # FastAPI entry point, static mount, CORS
│   ├── config.py                # pydantic-settings (env vars)
│   ├── models.py                # Pydantic request/response schemas
│   ├── routes/
│   │   ├── jobs.py              # POST /api/jobs, GET status, GET /stream (SSE), GET /download
│   │   └── languages.py         # GET /api/languages
│   └── services/
│       ├── pipeline.py          # Orchestrator — sequences all 8 stages
│       ├── youtube.py           # yt-dlp download
│       ├── audio_cleaner.py     # Demucs vocal separation (optional)
│       ├── transcriber.py       # faster-whisper transcription
│       ├── voice_sample.py      # Extract 45s clean voice sample
│       ├── voice_cloner.py      # ElevenLabs clone + cleanup
│       ├── translator.py        # Claude API translation with chunking
│       ├── tts.py               # ElevenLabs TTS with request stitching
│       └── audio_concat.py      # pydub MP3 concatenation
├── static/
│   ├── index.html               # Single-page UI
│   ├── style.css
│   └── app.js                   # SSE, form handling, progress UI
└── output/                      # Runtime job artifacts
    └── {job_id}/
```

## API Endpoints
- `POST /api/jobs` — submit job (youtube_url, target_language, API keys)
- `GET /api/jobs/{id}` — poll status
- `GET /api/jobs/{id}/stream` — SSE real-time progress
- `GET /api/jobs/{id}/download` — download final MP3
- `GET /api/languages` — supported target languages list

## Key Implementation Details

**Voice cloning lifecycle:** Create per job → use for TTS → delete after completion (avoids clutter in user's ElevenLabs account).

**TTS chunking:** Split translated text at sentence boundaries (~4500 chars/chunk). Use ElevenLabs `previous_request_ids` (up to 3) + `next_text` for seamless prosody across chunks.

**API keys:** Accepted per-request from the UI (stored in browser localStorage). Env fallback for single-user mode.

**Whisper model:** `base` by default (150MB, fast on CPU). User can upgrade to `small`/`medium` in advanced options.

**Demucs:** Opt-in only (slow on CPU). For clean audiobook audio, skip it.

## Implementation Order
1. Project setup: venv, requirements, .gitignore, .env.example
2. FastAPI skeleton: main.py, config, static mount
3. Service modules (one at a time, testable independently):
   - youtube.py (download)
   - transcriber.py (whisper)
   - voice_sample.py (extract clip)
   - voice_cloner.py (ElevenLabs clone)
   - translator.py (Claude API)
   - tts.py (ElevenLabs TTS + stitching)
   - audio_concat.py (pydub merge)
   - audio_cleaner.py (Demucs, last since optional)
4. pipeline.py — wire all services together with progress callbacks
5. routes/jobs.py — API endpoints + SSE streaming
6. Frontend: index.html + style.css + app.js
7. End-to-end test with a short YouTube clip

## Prerequisites (user must do)
1. **ElevenLabs account** — paid plan required for voice cloning (Starter $5/mo minimum)
2. **Anthropic API key** — from console.anthropic.com
3. **System deps:** `sudo apt install ffmpeg python3 python3-venv`

## Verification
- Run server: `uvicorn app.main:app --reload`
- Open `http://localhost:8000`
- Test with a short (<2 min) YouTube spoken-word video
- Verify: download works, cloned voice sounds like original, translation is correct
