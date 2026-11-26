from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db_compat import exact_string_equal
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate


# CREATE
def create_role(db: Session, role_data: RoleCreate):
    existing_role = db.scalar(
        select(Role).where(
            exact_string_equal(Role.role_name, role_data.role_name)
        )
    )

    if existing_role:
        raise ValueError("Role already exists")

    new_role = Role(role_name=role_data.role_name)

    try:
        db.add(new_role)
        db.commit()
        db.refresh(new_role)
        return new_role

    except IntegrityError:
        db.rollback()
        raise ValueError("Role already exists")


# GET ALL
def get_all_roles(db: Session):
    statement = select(Role).order_by(Role.role_id)
    return db.scalars(statement).all()


# GET BY ID
def get_role_by_id(db: Session, role_id: int):
    return db.get(Role, role_id)


# UPDATE
def update_role(
    db: Session,
    role_id: int,
    role_data: RoleUpdate
):
    role = db.get(Role, role_id)

    if role is None:
        return None

    existing_role = db.scalar(
        select(Role).where(
            exact_string_equal(Role.role_name, role_data.role_name),
            Role.role_id != role_id
        )
    )

    if existing_role:
        raise ValueError("Role name already exists")

    role.role_name = role_data.role_name

    try:
        db.commit()
        db.refresh(role)
        return role

    except IntegrityError:
        db.rollback()
        raise ValueError("Role name already exists")


# DELETE
def delete_role(db: Session, role_id: int):
    role = db.get(Role, role_id)

    if role is None:
        return False

    try:
        db.delete(role)
        db.commit()
        return True

    except IntegrityError:
        db.rollback()
        raise RuntimeError(
            "Cannot delete this role because employees are assigned to it"
        )