from fastapi import APIRouter
from celery.result import AsyncResult

from models import ProjectRequest, ProjectStatus
from tasks import celery, process_project

router = APIRouter(prefix="/project", tags=["projects"])


@router.post("", response_model=ProjectStatus)
def create_project(request: ProjectRequest):
    result = process_project.delay(request.model_dump())
    return ProjectStatus(job_id=result.id, status="pending")


@router.get("/{project_id}", response_model=ProjectStatus)
def get_project(project_id: str):
    result = AsyncResult(project_id, app=celery)
    state = result.state

    if state == "PENDING":
        return ProjectStatus(job_id=project_id, status="pending")
    elif state == "STARTED":
        return ProjectStatus(job_id=project_id, status="processing")
    elif state == "SUCCESS":
        data = result.result or {}
        return ProjectStatus(
            job_id=project_id,
            status="completed",
            clips_analyzed=data.get("clips_analyzed", 0),
            clips_selected=data.get("clips_selected", 0),
            output_url=data.get("output_url"),
        )
    elif state == "FAILURE":
        return ProjectStatus(job_id=project_id, status="failed")
    else:
        return ProjectStatus(job_id=project_id, status="pending")
