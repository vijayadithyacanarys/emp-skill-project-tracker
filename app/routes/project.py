from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.authorization import (
    project_scope_filter,
    require_admin_permission,
    require_permission,
    require_project_access,
)
from app.models.employee import Employee
from app.models.project import Project
from app.schemas.project import (
    ProjectCreate,
    ProjectManagerAssignmentCreate,
    ProjectManagerResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.rbac_assignment_service import (
    assign_project_manager,
    get_project_managers,
    remove_project_manager,
)
from app.services.project_service import (
    create_project,
    delete_project,
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
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("project:create")),
):
    return create_project(db, project_data)


@router.get(
    "/",
    response_model=list[ProjectResponse]
)
def get_all_projects_endpoint(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(
        require_permission("project:read")
    ),
):
    return db.scalars(
        select(Project)
        .where(project_scope_filter(db, current_employee))
        .order_by(Project.project_name)
    ).all()


@router.get(
    "/{project_id}",
    response_model=ProjectResponse
)
def get_project_by_id_endpoint(
    _actor: Employee = Depends(require_permission("project:read")),
    authorized_project: Project = Depends(require_project_access),
):
    return authorized_project


@router.put(
    "/{project_id}",
    response_model=ProjectResponse
)
def update_project_endpoint(
    project_id: UUID,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("project:update")),
    _authorized_project: Project = Depends(require_project_access),
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
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("project:delete")),
    _authorized_project: Project = Depends(require_project_access),
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


@router.post(
    "/{project_id}/managers",
    response_model=ProjectManagerResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_project_manager_endpoint(
    project_id: UUID,
    assignment: ProjectManagerAssignmentCreate,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("role:assign")
    ),
):
    try:
        return assign_project_manager(
            db,
            project_id,
            assignment.manager_id,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "/{project_id}/managers",
    response_model=list[ProjectManagerResponse],
)
def get_project_managers_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("role:read")
    ),
    _authorized_project: Project = Depends(require_project_access),
):
    try:
        return get_project_managers(db, project_id)
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.delete(
    "/{project_id}/managers/{manager_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_project_manager_endpoint(
    project_id: UUID,
    manager_id: UUID,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("role:assign")
    ),
):
    try:
        removed = remove_project_manager(db, project_id, manager_id)
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project manager assignment not found",
        )
