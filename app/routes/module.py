from typing import NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.authorization import (
    employee_has_role,
    require_admin_permission,
    require_permission,
)
from app.models.employee import Employee
from app.schemas.module import ModuleCreate, ModuleResponse, ModuleUpdate
from app.services.module_service import (
    activate_module,
    create_module,
    deactivate_module,
    get_active_modules_by_skill,
    get_active_modules_for_employee_skill_gaps,
    get_active_modules_for_manager,
    get_all_modules,
    get_module_by_id,
    get_module_by_skill,
    update_module,
)


router = APIRouter(
    prefix="/modules",
    tags=["Modules"],
)


def _raise_service_error(error: LookupError | ValueError) -> NoReturn:
    if isinstance(error, LookupError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=str(error),
    ) from error


def _require_manager_or_admin(db: Session, employee: Employee) -> None:
    if not (
        employee_has_role(db, employee.employee_id, "Manager")
        or employee_has_role(db, employee.employee_id, "Admin")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager role required",
        )


@router.post(
    "/",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_module_endpoint(
    module_data: ModuleCreate,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("skill:create")
    ),
) -> ModuleResponse:
    try:
        return create_module(db, module_data)
    except (LookupError, ValueError) as error:
        _raise_service_error(error)


@router.get(
    "/",
    response_model=list[ModuleResponse],
)
def get_all_modules_endpoint(
    skill_id: int | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("skill:read")
    ),
) -> list[ModuleResponse]:
    return get_all_modules(db, skill_id=skill_id, is_active=is_active)


@router.get(
    "/active",
    response_model=list[ModuleResponse],
)
def get_active_modules_endpoint(
    db: Session = Depends(get_db),
    actor: Employee = Depends(require_permission("skill:read")),
) -> list[ModuleResponse]:
    _require_manager_or_admin(db, actor)
    return get_active_modules_for_manager(db)


@router.get(
    "/active/by-skill/{skill_id}",
    response_model=list[ModuleResponse],
)
def get_active_modules_by_skill_endpoint(
    skill_id: int,
    db: Session = Depends(get_db),
    actor: Employee = Depends(require_permission("skill:read")),
) -> list[ModuleResponse]:
    _require_manager_or_admin(db, actor)
    try:
        return get_active_modules_by_skill(db, skill_id)
    except LookupError as error:
        _raise_service_error(error)


@router.get(
    "/active/{module_id}",
    response_model=ModuleResponse,
)
def get_active_module_by_id_endpoint(
    module_id: UUID,
    db: Session = Depends(get_db),
    actor: Employee = Depends(require_permission("skill:read")),
) -> ModuleResponse:
    _require_manager_or_admin(db, actor)
    module = get_module_by_id(db, module_id)
    if module is None or not module.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active module not found",
        )
    return module


@router.get(
    "/my/skill-gaps",
    response_model=list[ModuleResponse],
)
def get_my_skill_gap_modules_endpoint(
    db: Session = Depends(get_db),
    employee: Employee = Depends(require_permission("skill:read")),
) -> list[ModuleResponse]:
    return get_active_modules_for_employee_skill_gaps(db, employee)


@router.get(
    "/by-skill/{skill_id}",
    response_model=ModuleResponse,
)
def get_module_by_skill_endpoint(
    skill_id: int,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("skill:read")
    ),
) -> ModuleResponse:
    module = get_module_by_skill(db, skill_id)
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found for skill",
        )
    return module


@router.get(
    "/{module_id}",
    response_model=ModuleResponse,
)
def get_module_by_id_endpoint(
    module_id: UUID,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("skill:read")
    ),
) -> ModuleResponse:
    module = get_module_by_id(db, module_id)
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )
    return module


@router.patch(
    "/{module_id}",
    response_model=ModuleResponse,
)
def update_module_endpoint(
    module_id: UUID,
    module_data: ModuleUpdate,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("skill:update")
    ),
) -> ModuleResponse:
    try:
        module = update_module(db, module_id, module_data)
    except (LookupError, ValueError) as error:
        _raise_service_error(error)

    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )
    return module


@router.post(
    "/{module_id}/activate",
    response_model=ModuleResponse,
)
def activate_module_endpoint(
    module_id: UUID,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("skill:update")
    ),
) -> ModuleResponse:
    module = activate_module(db, module_id)
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )
    return module


@router.post(
    "/{module_id}/deactivate",
    response_model=ModuleResponse,
)
def deactivate_module_endpoint(
    module_id: UUID,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("skill:update")
    ),
) -> ModuleResponse:
    module = deactivate_module(db, module_id)
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )
    return module
