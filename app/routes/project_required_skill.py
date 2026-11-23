from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.project import ProjectResponse
from app.schemas.project_required_skill import (
    ProjectRequiredSkillCreate,
    ProjectRequiredSkillResponse,
    ProjectRequiredSkillUpdate
)
from app.services.project_required_skill_service import (
    add_required_skill,
    get_project_required_skills,
    get_projects_requiring_skill,
    remove_requirement,
    update_requirement
)


router = APIRouter(tags=["Project Required Skills"])


@router.post(
    "/projects/{project_id}/required-skills/",
    response_model=ProjectRequiredSkillResponse,
    status_code=status.HTTP_201_CREATED
)
def add_required_skill_endpoint(
    project_id: UUID,
    requirement_data: ProjectRequiredSkillCreate,
    db: Session = Depends(get_db)
):
    try:
        return add_required_skill(db, project_id, requirement_data)
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        ) from error


@router.get(
    "/projects/{project_id}/required-skills/",
    response_model=list[ProjectRequiredSkillResponse]
)
def get_project_required_skills_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    try:
        return get_project_required_skills(db, project_id)
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        ) from error


@router.patch(
    "/projects/{project_id}/required-skills/{skill_id}",
    response_model=ProjectRequiredSkillResponse
)
def update_requirement_endpoint(
    project_id: UUID,
    skill_id: int,
    requirement_data: ProjectRequiredSkillUpdate,
    db: Session = Depends(get_db)
):
    requirement = update_requirement(
        db,
        project_id,
        skill_id,
        requirement_data
    )

    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project skill requirement not found"
        )

    return requirement


@router.delete(
    "/projects/{project_id}/required-skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_requirement_endpoint(
    project_id: UUID,
    skill_id: int,
    db: Session = Depends(get_db)
):
    removed = remove_requirement(db, project_id, skill_id)

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project skill requirement not found"
        )


@router.get(
    "/skills/{skill_id}/required-projects/",
    response_model=list[ProjectResponse]
)
def get_projects_requiring_skill_endpoint(
    skill_id: int,
    db: Session = Depends(get_db)
):
    try:
        return get_projects_requiring_skill(db, skill_id)
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        ) from error
