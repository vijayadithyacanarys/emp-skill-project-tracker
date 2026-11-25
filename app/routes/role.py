from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.authorization import (
    require_admin_permission,
    require_permission,
)
from app.models.employee import Employee
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse
)
from app.services.role_service import (
    create_role,
    get_all_roles,
    get_role_by_id,
    update_role,
    delete_role
)


router = APIRouter(
    prefix="/roles",
    tags=["Roles"]
)


# CREATE ROLE
@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED
)
def create_role_endpoint(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("role:assign")
    ),
):
    try:
        return create_role(db, role_data)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


# GET ALL ROLES
@router.get(
    "/",
    response_model=list[RoleResponse]
)
def get_all_roles_endpoint(
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("role:read")),
):
    return get_all_roles(db)


# GET ROLE BY ID
@router.get(
    "/{role_id}",
    response_model=RoleResponse
)
def get_role_by_id_endpoint(
    role_id: int,
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("role:read")),
):
    role = get_role_by_id(db, role_id)

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    return role


# UPDATE ROLE
@router.put(
    "/{role_id}",
    response_model=RoleResponse
)
def update_role_endpoint(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("role:assign")
    ),
):
    try:
        role = update_role(db, role_id, role_data)

        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )

        return role

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


# DELETE ROLE
@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_role_endpoint(
    role_id: int,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("role:assign")
    ),
):
    try:
        deleted = delete_role(db, role_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )