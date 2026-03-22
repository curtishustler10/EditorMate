import os
import tempfile
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

from config import settings
from models import ClipInfo


class ClipAnalyzer:
    def __init__(self):
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def extract_frames(self, video_path: str, num_frames: int = 5) -> list[str]:
        from moviepy.editor import VideoFileClip

        clip = VideoFileClip(video_path)
        duration = clip.duration
        interval = duration / (num_frames + 1)

        frame_paths: list[str] = []
        tmp_dir = tempfile.mkdtemp()

        for i in range(1, num_frames + 1):
            t = interval * i
            frame = clip.get_frame(t)
            img = Image.fromarray(frame)
            frame_path = os.path.join(tmp_dir, f"frame_{i:03d}.jpg")
            img.save(frame_path, "JPEG", quality=85)
            frame_paths.append(frame_path)

        clip.close()
        return frame_paths

    def analyze_clip(self, frame_paths: list[str]) -> str:
        parts = []
        for frame_path in frame_paths:
            with open(frame_path, "rb") as f:
                image_bytes = f.read()
            parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

        parts.append(
            "These are frames sampled from a video clip. "
            "Describe what is happening in the clip concisely in 1-2 sentences, "
            "focusing on the main subject, action, and visual style."
        )

        response = self._client.models.generate_content(
            model="gemini-1.5-flash",
            contents=parts,
        )
        return response.text.strip()

    def analyze_all(self, clips_folder: str) -> list[ClipInfo]:
        from moviepy.editor import VideoFileClip

        video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
        clip_paths = sorted(
            p
            for p in Path(clips_folder).iterdir()
            if p.suffix.lower() in video_extensions
        )

        results: list[ClipInfo] = []

        for clip_path in clip_paths:
            video = VideoFileClip(str(clip_path))
            duration = video.duration
            video.close()

            frame_paths = self.extract_frames(str(clip_path))
            thumbnail_path = frame_paths[0] if frame_paths else None
            description = self.analyze_clip(frame_paths)

            results.append(
                ClipInfo(
                    path=str(clip_path),
                    duration=duration,
                    description=description,
                    thumbnail_path=thumbnail_path,
                )
            )

        return results
