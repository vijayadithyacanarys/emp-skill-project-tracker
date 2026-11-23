from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import (
    create_project,
    delete_project,
    get_all_projects,
    get_project_by_id,
    update_project
)


router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED
)
def create_project_endpoint(
    project_data: ProjectCreate,
    db: Session = Depends(get_db)
):
    return create_project(db, project_data)


@router.get(
    "/",
    response_model=list[ProjectResponse]
)
def get_all_projects_endpoint(
    db: Session = Depends(get_db)
):
    return get_all_projects(db)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse
)
def get_project_by_id_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    project = get_project_by_id(db, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return project


@router.put(
    "/{project_id}",
    response_model=ProjectResponse
)
def update_project_endpoint(
    project_id: UUID,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db)
):
    project = update_project(db, project_id, project_data)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_project_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    try:
        deleted = delete_project(db, project_id)
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        ) from error

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
