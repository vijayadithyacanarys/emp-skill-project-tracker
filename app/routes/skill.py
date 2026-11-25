from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.authorization import require_permission
from app.models.employee import Employee
from app.schemas.skill import (
    SkillCreate,
    SkillUpdate,
    SkillResponse
)
from app.services.skill_service import (
    create_skill,
    get_all_skills,
    get_skill_by_id,
    update_skill,
    delete_skill
)


router = APIRouter(
    prefix="/skills",
    tags=["Skills"]
)


# CREATE SKILL
@router.post(
    "/",
    response_model=SkillResponse,
    status_code=status.HTTP_201_CREATED
)
def create_skill_endpoint(
    skill_data: SkillCreate,
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("skill:create")),
):
    try:
        return create_skill(db, skill_data)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


# GET ALL SKILLS
@router.get(
    "/",
    response_model=list[SkillResponse]
)
def get_all_skills_endpoint(
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("skill:read")),
):
    return get_all_skills(db)


# GET SKILL BY ID
@router.get(
    "/{skill_id}",
    response_model=SkillResponse
)
def get_skill_by_id_endpoint(
    skill_id: int,
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("skill:read")),
):
    skill = get_skill_by_id(db, skill_id)

    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )

    return skill


# UPDATE SKILL
@router.put(
    "/{skill_id}",
    response_model=SkillResponse
)
def update_skill_endpoint(
    skill_id: int,
    skill_data: SkillUpdate,
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("skill:update")),
):
    try:
        skill = update_skill(db, skill_id, skill_data)

        if skill is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found"
            )

        return skill

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


# DELETE SKILL
@router.delete(
    "/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_skill_endpoint(
    skill_id: int,
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("skill:delete")),
):
    try:
        deleted = delete_skill(db, skill_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found"
            )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )