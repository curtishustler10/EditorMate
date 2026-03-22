import os
import uuid
import urllib.request
import tempfile

from celery import Celery

from config import settings
from services.audio_analyzer import AudioAnalyzer
from services.scene_detector import SceneDetector
from services.caption_generator import CaptionGenerator
from services.video_processor import VideoProcessor
from services.storage import StorageService
from services.clip_analyzer import ClipAnalyzer
from services.clip_selector import ClipSelector
from services.voiceover_generator import VoiceoverGenerator

celery = Celery("editormate", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
)


def _download_media(url: str, dest_path: str) -> None:
    urllib.request.urlretrieve(url, dest_path)


@celery.task(bind=True, name="tasks.process_video")
def process_video(self, media_url: str, options_dict: dict) -> str:
    """
    Main processing pipeline:
      1. Download media from media_url
      2. Extract audio
      3. Detect beats
      4. Detect scenes
      5. Generate and burn captions if requested
      6. Apply edits (background music)
      7. Upload result to R2
      8. Return output URL
    """
    temp_files = []

    try:
        work_dir = tempfile.mkdtemp(prefix="editormate_")

        # 1. Download media
        ext = os.path.splitext(media_url.split("?")[0])[-1] or ".mp4"
        video_path = os.path.join(work_dir, f"input{ext}")
        _download_media(media_url, video_path)
        temp_files.append(video_path)

        # 2. Extract audio
        audio_path = os.path.join(work_dir, "audio.wav")
        analyzer = AudioAnalyzer()
        analyzer.extract_audio(video_path, audio_path)
        temp_files.append(audio_path)

        # 3. Detect beats
        beats = analyzer.detect_beats(audio_path)

        # 4. Detect scenes
        detector = SceneDetector()
        scenes = detector.detect_scenes(video_path)

        # Build cut list from scenes (fall back to full clip if no scenes found)
        cuts = scenes if scenes else [(0, None)]

        processor = VideoProcessor()
        processor.apply_cuts(video_path, cuts)

        # 5. Generate captions if requested
        srt_path = None
        if options_dict.get("add_captions"):
            caption_gen = CaptionGenerator()
            transcript = caption_gen.transcribe(video_path)
            srt_content = caption_gen.generate_srt(transcript)
            srt_path = os.path.join(work_dir, "captions.srt")
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_content)
            temp_files.append(srt_path)

            captioned_path = os.path.join(work_dir, "captioned.mp4")
            temp_files.append(captioned_path)
            processor.add_captions(video_path, srt_path, captioned_path)

        # 6. Apply background music if provided
        background_music = options_dict.get("background_music")
        if background_music:
            music_path = os.path.join(work_dir, "music" + os.path.splitext(background_music)[-1])
            _download_media(background_music, music_path)
            temp_files.append(music_path)
            processor.add_music(video_path, music_path)

        # Render final output
        output_path = os.path.join(work_dir, "output.mp4")
        temp_files.append(output_path)
        processor.render(output_path)

        # 7. Upload to R2
        storage = StorageService()
        remote_name = f"outputs/{uuid.uuid4()}.mp4"
        storage.upload_file(output_path, remote_name)

        # 8. Return signed output URL
        output_url = storage.get_signed_url(remote_name)
        return output_url

    finally:
        cleanup.delay(temp_files)


@celery.task(bind=True, name="tasks.process_project")
def process_project(self, request_dict: dict) -> dict:
    """
    Multi-clip project pipeline:
      1. Scan clips_folder
      2. ClipAnalyzer.analyze_all()
      3. ClipSelector.select_and_order()
      4. AudioAnalyzer.detect_beats() on provided audio (or extracted audio)
      5. Align cut points to beats
      6. VideoProcessor.apply_cuts_multi_clip()
      7. Add voiceover if requested
      8. Add background music if provided
      9. Render, upload, return URL
    """
    temp_files = []

    try:
        work_dir = tempfile.mkdtemp(prefix="editormate_project_")

        clips_folder = request_dict["clips_folder"]
        audio_file = request_dict.get("audio_file")
        prompt = request_dict["prompt"]
        aspect_ratio = tuple(request_dict.get("aspect_ratio", [16, 9]))
        voiceover_script = request_dict.get("voiceover")

        # 1 + 2. Scan and analyze all clips
        analyzer = ClipAnalyzer()
        clips = analyzer.analyze_all(clips_folder)

        # 3. Select and order clips via Claude
        selector = ClipSelector()
        selected = selector.select_and_order(clips, prompt)

        # 4. Detect beats on the provided audio (or the first selected clip's audio)
        audio_analyzer = AudioAnalyzer()
        beat_source = audio_file
        if not beat_source and selected:
            beat_source_wav = os.path.join(work_dir, "beat_source.wav")
            audio_analyzer.extract_audio(selected[0].path, beat_source_wav)
            temp_files.append(beat_source_wav)
            beat_source = beat_source_wav

        beats: list[float] = audio_analyzer.detect_beats(beat_source) if beat_source else []

        # 5. Align cut points to beats
        def _snap_to_beat(t: float, beat_times: list[float]) -> float:
            if not beat_times:
                return t
            return min(beat_times, key=lambda b: abs(b - t))

        cuts_list: list[tuple[str, float, float]] = []
        for clip in selected:
            in_t = _snap_to_beat(clip.in_time, beats)
            out_t = _snap_to_beat(clip.out_time, beats)
            if out_t <= in_t:
                out_t = clip.out_time  # fallback to unsnapped if snapping collapsed the segment
            cuts_list.append((clip.path, in_t, out_t))

        # 6. Build concatenated clip
        processor = VideoProcessor()
        processor.apply_cuts_multi_clip(cuts_list)

        # 7. Add voiceover if requested
        if voiceover_script:
            vo_gen = VoiceoverGenerator()
            vo_path = vo_gen.generate(voiceover_script)
            temp_files.append(vo_path)
            processor.add_music("", vo_path, fade_duration=0.5)

        # 8. Add background music if provided
        if audio_file:
            processor.add_music("", audio_file)

        # Render
        output_path = os.path.join(work_dir, "project_output.mp4")
        temp_files.append(output_path)
        processor.render(output_path)

        # 9. Upload and return URL
        storage = StorageService()
        remote_name = f"outputs/{uuid.uuid4()}.mp4"
        storage.upload_file(output_path, remote_name)
        output_url = storage.get_signed_url(remote_name)

        return {
            "clips_analyzed": len(clips),
            "clips_selected": len(selected),
            "output_url": output_url,
        }

    finally:
        cleanup.delay(temp_files)


@celery.task(name="tasks.cleanup")
def cleanup(temp_files: list) -> None:
    """Remove temporary files created during processing."""
    for path in temp_files:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
