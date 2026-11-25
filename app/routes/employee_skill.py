from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.authorization import (
    require_employee_access,
    require_permission,
)
from app.models.employee import Employee

from app.schemas.employee_skill import (
    EmployeeSkillCreate,
    EmployeeSkillUpdate,
    EmployeeSkillResponse
)

from app.services.employee_skill_service import (
    assign_skill,
    get_employee_skills,
    get_employee_skill,
    update_employee_skill,
    remove_employee_skill
)


router = APIRouter(
    prefix="/employees/{employee_id}/skills",
    tags=["Employee Skills"]
)


# ASSIGN SKILL
@router.post(
    "/",
    response_model=EmployeeSkillResponse,
    status_code=status.HTTP_201_CREATED
)
def assign_skill_endpoint(
    employee_id: UUID,
    skill_data: EmployeeSkillCreate,
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("skill:create")),
    _authorized_employee: Employee = Depends(require_employee_access),
):
    try:
        return assign_skill(db, employee_id, skill_data)

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


# GET ALL EMPLOYEE SKILLS
@router.get(
    "/",
    response_model=list[EmployeeSkillResponse]
)
def get_employee_skills_endpoint(
    employee_id: UUID,
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("skill:read")),
    _authorized_employee: Employee = Depends(require_employee_access),
):
    try:
        return get_employee_skills(db, employee_id)

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


# GET PARTICULAR EMPLOYEE SKILL
@router.get(
    "/{skill_id}",
    response_model=EmployeeSkillResponse
)
def get_employee_skill_endpoint(
    employee_id: UUID,
    skill_id: int,
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("skill:read")),
    _authorized_employee: Employee = Depends(require_employee_access),
):
    assignment = get_employee_skill(
        db,
        employee_id,
        skill_id
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee skill assignment not found"
        )

    return assignment


# UPDATE EMPLOYEE SKILL
@router.put(
    "/{skill_id}",
    response_model=EmployeeSkillResponse
)
def update_employee_skill_endpoint(
    employee_id: UUID,
    skill_id: int,
    skill_data: EmployeeSkillUpdate,
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("skill:update")),
    _authorized_employee: Employee = Depends(require_employee_access),
):
    try:
        assignment = update_employee_skill(
            db,
            employee_id,
            skill_id,
            skill_data
        )

        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee skill assignment not found"
            )

        return assignment

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


# REMOVE EMPLOYEE SKILL
@router.delete(
    "/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_employee_skill_endpoint(
    employee_id: UUID,
    skill_id: int,
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("skill:delete")),
    _authorized_employee: Employee = Depends(require_employee_access),
):
    deleted = remove_employee_skill(
        db,
        employee_id,
        skill_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee skill assignment not found"
        )