# EditorMate

# 🎬 AutoCut — Automated Video Editing Tool

> A CapCut-style automated video editing engine built with FFmpeg, Python, and AI — designed for programmatic, queue-driven video production at scale.

-----

## 📌 Overview

AutoCut is a backend-first, AI-augmented video editing system that replicates core CapCut features programmatically. It accepts raw video input and a JSON edit specification, then returns a fully processed, export-ready MP4.

Built for creators, agencies, and SaaS products that need automated video production without manual editing.

-----

## ✨ Features

|Feature                  |Implementation                   |
|-------------------------|---------------------------------|
|Auto captions / subtitles|Whisper (self-hosted)            |
|Text-to-speech voiceover |ElevenLabs / Kokoro TTS          |
|Background removal       |rembg + frame extraction         |
|Beat-synced cuts         |librosa BPM detection            |
|Scene detection          |PySceneDetect                    |
|Smart crop / reframe     |MediaPipe + FFmpeg               |
|Template overlays        |Remotion (React-based renderer)  |
|AI clip generation       |Luma Dream Machine / Kling API   |
|Music sync               |librosa + FFmpeg filter chain    |
|Auto highlight reel      |Whisper + LLM transcript analysis|

-----

## 🏗️ Architecture

```
User uploads video
       ↓
REST API (FastAPI)
       ↓
Job Queue (BullMQ / Redis)
       ↓
Worker Node
  ├── Whisper        → transcript + SRT captions
  ├── PySceneDetect  → scene list
  ├── librosa        → BPM / beat grid
  ├── FFmpeg         → cuts, transitions, filters, audio mix
  ├── Remotion       → text overlays, title cards, templates
  └── rembg          → background removal (optional)
       ↓
Output MP4 → Upload to Cloudflare R2
       ↓
Return signed URL to client
```

-----

## 🧱 Tech Stack

### Backend

- **Python 3.11+** — core processing runtime
- **FastAPI** — REST API layer
- **Celery + Redis** — job queue and worker orchestration
- **FFmpeg** — video/audio processing engine
- **MoviePy** — high-level Python video editing API
- **Whisper** — local speech-to-text / auto-captioning
- **PySceneDetect** — automatic scene boundary detection
- **librosa** — audio analysis, BPM detection, beat tracking
- **MediaPipe** — face/body tracking for smart reframe
- **rembg** — AI background removal per frame

### Rendering

- **Remotion** — React-based programmatic video renderer
- **Node.js 18+** — Remotion runtime

### Storage & Infrastructure

- **Cloudflare R2** — video storage (S3-compatible)
- **Redis** — queue backend + ephemeral job state
- **DigitalOcean Droplet** — CPU worker (standard jobs)
- **RunPod / Modal.com** — on-demand GPU (AI-heavy jobs)

### Frontend (Optional Web Editor)

- **React** — UI framework
- **ffmpeg.wasm** — in-browser preview processing
- **Fabric.js / Konva.js** — canvas-based overlay editor

-----

## 🚀 Getting Started

### Prerequisites

```bash
# System dependencies
sudo apt install ffmpeg python3.11 nodejs redis-server

# Python dependencies
pip install fastapi celery moviepy openai-whisper scenedetect librosa mediapipe rembg

# Node dependencies (for Remotion)
npm install -g remotion
```

### Environment Variables

```env
REDIS_URL=redis://localhost:6379
R2_ACCOUNT_ID=your_cloudflare_account_id
R2_ACCESS_KEY=your_r2_access_key
R2_SECRET_KEY=your_r2_secret_key
R2_BUCKET=autocut-videos
ELEVENLABS_API_KEY=your_elevenlabs_key
LUMA_API_KEY=your_luma_key
```

### Run the API

```bash
# Start Redis
redis-server

# Start FastAPI
uvicorn main:app --reload --port 8000

# Start Celery worker
celery -A tasks worker --loglevel=info
```

-----

## 📡 API Reference

### `POST /edit`

Submit a video for automated editing.

**Request:**

```json
{
  "video_url": "https://r2.yourdomain.com/raw/input.mp4",
  "options": {
    "captions": true,
    "beat_sync": true,
    "background_remove": false,
    "template": "cinematic_lower_third",
    "music_url": "https://r2.yourdomain.com/music/track.mp3",
    "aspect_ratio": "9:16",
    "output_format": "mp4"
  }
}
```

**Response:**

```json
{
  "job_id": "abc123",
  "status": "queued",
  "estimated_seconds": 45
}
```

-----

### `GET /job/{job_id}`

Poll job status.

```json
{
  "job_id": "abc123",
  "status": "complete",
  "output_url": "https://r2.yourdomain.com/output/abc123.mp4",
  "duration_seconds": 38
}
```

-----

## 🗺️ Roadmap

- [x] FFmpeg wrapper API
- [x] Whisper auto-captions (SRT + hardburn)
- [x] Beat-synced cut detection
- [x] Remotion template overlays
- [ ] Web-based timeline editor
- [ ] Multi-template library
- [ ] Social format presets (Reels, TikTok, YouTube Shorts)
- [ ] Auto B-roll insertion via AI generation
- [ ] Batch processing endpoint
- [ ] Webhook callbacks on job completion

-----

## 📁 Project Structure

```
autocut/
├── api/
│   ├── main.py              # FastAPI app entry point
│   ├── routes/
│   │   ├── edit.py          # /edit endpoint
│   │   └── jobs.py          # /job status endpoint
│   └── schemas.py           # Pydantic models
├── workers/
│   ├── tasks.py             # Celery task definitions
│   ├── ffmpeg_pipeline.py   # FFmpeg wrapper logic
│   ├── caption_engine.py    # Whisper integration
│   ├── beat_sync.py         # librosa beat detection
│   ├── scene_detector.py    # PySceneDetect wrapper
│   └── bg_remover.py        # rembg frame processor
├── remotion/
│   ├── src/
│   │   ├── templates/       # Remotion video templates
│   │   └── index.tsx        # Remotion entry point
│   └── package.json
├── storage/
│   └── r2_client.py         # Cloudflare R2 upload/download
├── .env.example
├── docker-compose.yml
└── README.md
```

-----

## 🐳 Docker

```bash
docker-compose up --build
```

`docker-compose.yml` spins up: FastAPI, Celery worker, and Redis.

-----

## 📄 License

MIT — use freely, attribution appreciated.

-----

## 🤝 Contributing

PRs welcome. Open an issue first for major changes.

-----

*Built with FFmpeg, Whisper, Remotion, and Python.*
