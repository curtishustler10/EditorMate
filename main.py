from fastapi import FastAPI
from celery.result import AsyncResult

from config import settings
from models import EditRequest, JobResponse, JobStatus
from tasks import celery, process_video
from routers import projects

app = FastAPI(title="EditorMate")

app.include_router(projects.router)


@app.get("/")
def root():
    return {"name": "EditorMate", "version": "1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/edit", response_model=JobResponse)
def edit(request: EditRequest):
    result = process_video.delay(request.input_url, request.options.model_dump())
    return JobResponse(job_id=result.id, status=JobStatus.pending)


@app.get("/job/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    result = AsyncResult(job_id, app=celery)

    state = result.state

    if state == "PENDING":
        return JobResponse(job_id=job_id, status=JobStatus.pending)
    elif state == "STARTED":
        return JobResponse(job_id=job_id, status=JobStatus.processing)
    elif state == "SUCCESS":
        return JobResponse(job_id=job_id, status=JobStatus.completed, output_url=result.result)
    elif state == "FAILURE":
        return JobResponse(job_id=job_id, status=JobStatus.failed, error=str(result.result))
    else:
        return JobResponse(job_id=job_id, status=JobStatus.pending)
