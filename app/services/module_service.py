from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.employee_project_allocation import EmployeeProjectAllocation
from app.models.employee_skill import EmployeeSkill
from app.models.module import Module
from app.models.project_required_skill import ProjectRequiredSkill
from app.models.skill import Skill
from app.schemas.module import ModuleCreate, ModuleUpdate


def create_module(db: Session, module_data: ModuleCreate) -> Module:
    try:
        if db.get(Skill, module_data.skill_id) is None:
            raise LookupError("Skill not found")

        existing_module = db.scalar(
            select(Module.module_id).where(
                Module.skill_id == module_data.skill_id
            )
        )
        if existing_module is not None:
            raise ValueError("A module already exists for this skill")

        module = Module(**module_data.model_dump())
        db.add(module)
        db.commit()
        db.refresh(module)
        return module
    except IntegrityError as error:
        db.rollback()
        raise ValueError(
            "A module already exists for this skill or the skill no longer exists"
        ) from error
    except Exception:
        db.rollback()
        raise


def get_all_modules(
    db: Session,
    skill_id: int | None = None,
    is_active: bool | None = None,
):
    statement = select(Module)
    if skill_id is not None:
        statement = statement.where(Module.skill_id == skill_id)
    if is_active is not None:
        statement = statement.where(Module.is_active.is_(is_active))

    return db.scalars(
        statement.order_by(Module.module_name, Module.module_id)
    ).all()


def get_active_modules(db: Session):
    return get_all_modules(db, is_active=True)


def get_module_by_id(db: Session, module_id: UUID) -> Module | None:
    return db.get(Module, module_id)


def get_module_by_skill(db: Session, skill_id: int) -> Module | None:
    return db.scalar(select(Module).where(Module.skill_id == skill_id))


def get_active_modules_by_skill(db: Session, skill_id: int) -> list[Module]:
    if db.get(Skill, skill_id) is None:
        raise LookupError("Skill not found")
    return db.scalars(
        select(Module)
        .where(
            Module.skill_id == skill_id,
            Module.is_active.is_(True),
        )
        .order_by(Module.module_name)
    ).all()


def update_module(
    db: Session,
    module_id: UUID,
    module_data: ModuleUpdate,
) -> Module | None:
    try:
        module = db.scalar(
            select(Module)
            .where(Module.module_id == module_id)
            .with_for_update()
            .with_hint(Module, "WITH (UPDLOCK, ROWLOCK)", dialect_name="mssql")
        )
        if module is None:
            db.rollback()
            return None

        updates = module_data.model_dump(exclude_unset=True)
        new_skill_id = updates.get("skill_id")
        if new_skill_id is not None and new_skill_id != module.skill_id:
            if db.get(Skill, new_skill_id) is None:
                raise LookupError("Skill not found")
            existing_module = db.scalar(
                select(Module.module_id).where(
                    Module.skill_id == new_skill_id,
                    Module.module_id != module_id,
                )
            )
            if existing_module is not None:
                raise ValueError("A module already exists for this skill")

        for field, value in updates.items():
            setattr(module, field, value)
        db.commit()
        db.refresh(module)
        return module
    except IntegrityError as error:
        db.rollback()
        raise ValueError(
            "A module already exists for this skill or the skill no longer exists"
        ) from error
    except Exception:
        db.rollback()
        raise


def set_module_active(
    db: Session,
    module_id: UUID,
    is_active: bool,
) -> Module | None:
    try:
        module = db.scalar(
            select(Module)
            .where(Module.module_id == module_id)
            .with_for_update()
            .with_hint(Module, "WITH (UPDLOCK, ROWLOCK)", dialect_name="mssql")
        )
        if module is None:
            db.rollback()
            return None

        module.is_active = is_active
        db.commit()
        db.refresh(module)
        return module
    except Exception:
        db.rollback()
        raise


def activate_module(db: Session, module_id: UUID) -> Module | None:
    return set_module_active(db, module_id, True)


def deactivate_module(db: Session, module_id: UUID) -> Module | None:
    return set_module_active(db, module_id, False)


def get_active_modules_for_employee_skill_gaps(
    db: Session,
    employee: Employee,
) -> list[Module]:
    gap_skill_ids = (
        select(ProjectRequiredSkill.skill_id)
        .join(
            EmployeeProjectAllocation,
            EmployeeProjectAllocation.project_id
            == ProjectRequiredSkill.project_id,
        )
        .outerjoin(
            EmployeeSkill,
            and_(
                EmployeeSkill.employee_id == employee.employee_id,
                EmployeeSkill.skill_id == ProjectRequiredSkill.skill_id,
            ),
        )
        .where(
            EmployeeProjectAllocation.employee_id == employee.employee_id,
            EmployeeProjectAllocation.status.in_(("planned", "active")),
            or_(
                EmployeeSkill.employee_id.is_(None),
                EmployeeSkill.proficiency_level
                < ProjectRequiredSkill.minimum_proficiency,
            ),
        )
        .distinct()
    )
    return db.scalars(
        select(Module)
        .where(
            Module.is_active.is_(True),
            Module.skill_id.in_(gap_skill_ids),
        )
        .order_by(Module.module_name)
    ).all()


def get_active_modules_for_manager(db: Session) -> list[Module]:
    return get_active_modules(db)
