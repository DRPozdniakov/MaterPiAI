# MasterPi AI

YouTube videos to multilingual audiobooks with cloned voice. Built for the UCL Hackathon.

Paste a YouTube URL, pick a target language, and MasterPi generates an audiobook in the speaker's cloned voice — translated and synthesized end-to-end.

## How It Works

7-stage pipeline:

1. **Download** — Extract audio from YouTube (yt-dlp + FFmpeg)
2. **Transcribe** — Pull subtitles from the video (English preferred, auto-generated fallback)
3. **Extract Voice** — First 45s of audio as voice sample (pydub)
4. **Clone Voice** — Instant voice clone via ElevenLabs API
5. **Translate** — Chunked translation via Claude Sonnet (LangChain, 10k char chunks with context overlap)
6. **Synthesize** — Text-to-speech in target language using the cloned voice (ElevenLabs)
7. **Concatenate** — Merge MP3 chunks into final audiobook

Real-time progress via SSE streaming. Three pricing tiers: Short (12.5%), Medium (40%), Full (100%).

## Tech Stack

**Backend:** FastAPI, Pydantic, LangChain, httpx, yt-dlp, pydub, SSE
**Frontend:** React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui
**APIs:** ElevenLabs (TTS + voice cloning), Anthropic Claude (translation)

## Project Structure

```
app/
├── api/              # FastAPI routes (thin controllers)
│   ├── job_routes.py       # Job CRUD, SSE streaming, audio download
│   ├── video_routes.py     # Video analysis & cost breakdown
│   ├── language_routes.py  # Supported languages list
│   └── routes.py           # Health check
├── services/         # Business logic
│   ├── pipeline.py         # Master orchestrator (7-stage pipeline)
│   ├── youtube.py          # Video download via yt-dlp
│   ├── transcriber.py      # Subtitle extraction
│   ├── translator.py       # LangChain + Claude translation
│   ├── tts.py              # ElevenLabs TTS with sentence chunking
│   ├── voice_cloner.py     # ElevenLabs voice cloning
│   ├── voice_sample.py     # Audio sample extraction
│   ├── audio_concat.py     # MP3 concatenation
│   ├── cost_calculator.py  # Tier pricing logic
│   └── job_manager.py      # In-memory job state + SSE queues
├── models/           # Pydantic DTOs and enums
├── exceptions.py     # Custom exception hierarchy
├── dependencies.py   # Service factories for FastAPI Depends()
├── languages.py      # 29 supported languages
└── main.py           # FastAPI app, CORS, exception handlers
config/
└── settings.py       # Pydantic Settings (env-based)
ui/                   # React frontend
tests/                # Unit + integration tests
tools/                # CLI utilities (cost breakdown calculator)
```

## API Endpoints

```
GET  /api/v1/health              # Health check
POST /api/v1/videos/analyze      # Video info + cost breakdown per tier
GET  /api/v1/languages           # Supported languages (29)
POST /api/v1/jobs                # Create audiobook job
GET  /api/v1/jobs/{id}           # Job status
GET  /api/v1/jobs/{id}/stream    # SSE real-time progress
GET  /api/v1/jobs/{id}/audio     # Download completed MP3
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- FFmpeg installed and on PATH

### Backend

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### Frontend

```bash
cd ui
npm install
```

### Environment

```bash
cp .env.example .env
```

Fill in your API keys:

```env
ELEVENLABS_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
```

## Run

```bash
# Backend (port 8000)
python run.py

# Frontend (port 5173, proxies /api to backend)
cd ui && npm run dev
```

## Test

```bash
pytest tests/ -v
pytest tests/unit/ -v                              # Unit tests only
pytest tests/ --cov=app --cov-report=term-missing  # With coverage
```

## Supported Languages

English, Japanese, Chinese, German, Hindi, French, Korean, Portuguese, Italian, Spanish, Indonesian, Dutch, Turkish, Filipino, Polish, Swedish, Bulgarian, Romanian, Arabic, Czech, Greek, Finnish, Croatian, Malay, Slovak, Danish, Tamil, Ukrainian, Russian
