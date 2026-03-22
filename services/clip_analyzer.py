import base64
import os
import tempfile
from pathlib import Path

import anthropic
from PIL import Image

from config import settings
from models import ClipInfo


class ClipAnalyzer:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def extract_frames(self, video_path: str, num_frames: int = 5) -> list[str]:
        """
        Extract evenly-spaced frames from a video and save as JPEG files.

        :param video_path: Path to the source video file.
        :param num_frames: Number of frames to extract.
        :return: List of paths to extracted frame images.
        """
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
        """
        Describe video clip content using Claude Vision from extracted frames.

        :param frame_paths: Paths to frame image files.
        :return: Text description of the clip.
        """
        content: list[dict] = []

        for frame_path in frame_paths:
            with open(frame_path, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_data,
                    },
                }
            )

        content.append(
            {
                "type": "text",
                "text": (
                    "These are frames sampled from a video clip. "
                    "Describe what is happening in the clip concisely in 1-2 sentences, "
                    "focusing on the main subject, action, and visual style."
                ),
            }
        )

        message = self._client.messages.create(
            model="claude-opus-4-6",
            max_tokens=256,
            messages=[{"role": "user", "content": content}],
        )

        return message.content[0].text.strip()

    def analyze_all(self, clips_folder: str) -> list[ClipInfo]:
        """
        Analyze every video clip in a folder and return ClipInfo for each.

        :param clips_folder: Directory containing video files.
        :return: List of ClipInfo objects with path, duration, description, thumbnail.
        """
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
