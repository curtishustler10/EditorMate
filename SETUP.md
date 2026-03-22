# EditorMate Setup Guide (macOS)

## Prerequisites

1. **Python 3.10+** installed
2. **Homebrew** installed
3. **FFmpeg** for video processing

## Installation Steps

### 1. Install FFmpeg
```bash
brew install ffmpeg
```

### 2. Clone the Repository
```bash
git clone https://github.com/curtishustler10/EditorMate.git
cd EditorMate
```

### 3. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment

Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

Edit `.env` with your API keys:
- `REDIS_URL` - Your Redis Cloud connection string
- `R2_*` - Cloudflare R2 credentials
- `OPENAI_API_KEY` - For Whisper captions
- `ANTHROPIC_API_KEY` - For Claude Vision
- `GEMINI_API_KEY` - For Nanobanana
- `ELEVENLABS_API_KEY` - For TTS voiceover
- `LUMA_API_KEY` - Optional, for AI clips

### 6. Run the Application

**Development:**
```bash
python main.py
```
Server runs at `http://localhost:8000`

**With Celery (background tasks):**
```bash
# Terminal 1: Start Redis (or use cloud)
redis-server

# Terminal 2: Start Celery worker
celery -A tasks worker --loglevel=info

# Terminal 3: Start API
python main.py
```

## API Documentation

Once running, visit: `http://localhost:8000/docs`

### Endpoints

- `GET /` - Health check
- `GET /health` - API health status
- `POST /edit` - Submit video edit job
- `GET /job/{job_id}` - Get job status

### Example: Submit Edit Job
```bash
curl -X POST http://localhost:8000/edit \
  -H "Content-Type: application/json" \
  -d '{"input_url": "https://example.com/video.mp4", "options": {"model": "fast"}}'
```

## Troubleshooting

### FFmpeg not found
```bash
brew install ffmpeg
export PATH="/usr/local/opt/ffmpeg/bin:$PATH"
```

### Redis connection error
Verify your `REDIS_URL` in `.env` is correct.

### Module not found
```bash
pip install -r requirements.txt
```

## Tech Stack

- **FastAPI** - Web framework
- **Celery** - Background task processing
- **Redis** - Message broker
- **Claude Vision** - Scene analysis
- **OpenAI Whisper** - Audio transcription
- **MoviePy** - Video editing
- **Cloudflare R2** - Video storage
