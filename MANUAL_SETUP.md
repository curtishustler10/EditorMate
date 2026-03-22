# EditorMate - Manual Setup Required

## Needed from You (Curt)

1. **API Keys** (add to `.env`):
   - `ELEVENLABS_API_KEY` - for TTS voiceover
   - `LUMA_API_KEY` - for AI clip generation
   - `OPENAI_API_KEY` - for Whisper captions
   - `CLOUDFLARE_R2_*` - for video storage (R2 account, access key, secret key, bucket name)

2. **Infrastructure** (external):
   - Redis server (can use cloud service like Redis Cloud)
   - Cloudflare R2 bucket for video storage
   - GPU compute for AI-heavy jobs (RunPod, Modal.com, or DigitalOcean GPU droplet)

## What's Being Built

Claude Code will set up:
- Full FastAPI backend with all endpoints
- Celery task queue integration
- Video processing workers (FFmpeg, MoviePy)
- Audio analysis (librosa, beat detection)
- Scene detection (PySceneDetect)
- Background removal (rembg)
- Smart cropping (MediaPipe)
- Caption/subtitle generation (Whisper)
- Cloud storage integration (R2)
- Docker + docker-compose setup

## To Run Locally Later

```bash
# 1. Copy env and add your API keys
cp .env.example .env
nano .env

# 2. Install deps
pip install -r requirements.txt

# 3. Start Redis (or use cloud)
redis-server

# 4. Start API
uvicorn main:app --reload

# 5. Start worker (separate terminal)
celery -A tasks worker --loglevel=info
```
