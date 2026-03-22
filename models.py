from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ClipInfo(BaseModel):
    path: str
    duration: float
    description: str
    thumbnail_path: Optional[str] = None


class ProjectRequest(BaseModel):
    clips_folder: str
    audio_file: Optional[str] = None
    prompt: str
    aspect_ratio: tuple[int, int] = (16, 9)
    voiceover: Optional[str] = None


class ProjectStatus(BaseModel):
    job_id: str
    status: str
    clips_analyzed: int = 0
    clips_selected: int = 0
    output_url: Optional[str] = None


class EditOptions(BaseModel):
    trim_silence: bool = False
    normalize_audio: bool = False
    add_captions: bool = False
    background_music: Optional[str] = None


class EditRequest(BaseModel):
    input_url: str
    options: EditOptions = EditOptions()
    webhook_url: Optional[str] = None


class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    output_url: Optional[str] = None
    error: Optional[str] = None
