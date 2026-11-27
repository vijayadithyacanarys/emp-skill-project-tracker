from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.assignment import Assignment
from app.models.assignment_question import AssignmentQuestion
from app.models.employee import Employee
from app.models.employee_assignment import EmployeeAssignment
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate


def lock_assignment_for_update(
    db: Session,
    assignment_id: UUID,
) -> Assignment | None:
    statement = (
        select(Assignment)
        .where(Assignment.assignment_id == assignment_id)
        .with_for_update()
        .with_hint(
            Assignment,
            "WITH (UPDLOCK, ROWLOCK)",
            dialect_name="mssql",
        )
    )
    return db.scalar(statement)


def create_assignment(
    db: Session,
    assignment_data: AssignmentCreate,
) -> Assignment:
    assignment = Assignment(**assignment_data.model_dump())
    try:
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment
    except Exception:
        db.rollback()
        raise


def get_all_assignments(
    db: Session,
    is_active: bool | None = None,
) -> list[Assignment]:
    statement = select(Assignment)
    if is_active is not None:
        statement = statement.where(Assignment.is_active.is_(is_active))
    return db.scalars(
        statement.order_by(Assignment.title, Assignment.assignment_id)
    ).all()


def get_active_assignments(db: Session) -> list[Assignment]:
    return get_all_assignments(db, is_active=True)


def get_assignment_by_id(
    db: Session,
    assignment_id: UUID,
) -> Assignment | None:
    return db.get(Assignment, assignment_id)


def get_assignment_details(
    db: Session,
    assignment_id: UUID,
) -> Assignment | None:
    statement = (
        select(Assignment)
        .where(Assignment.assignment_id == assignment_id)
        .options(
            selectinload(Assignment.questions).selectinload(
                AssignmentQuestion.choices
            )
        )
    )
    assignment = db.scalar(statement)
    if assignment is not None:
        assignment.questions.sort(
            key=lambda question: (
                question.question_order,
                question.question_id,
            )
        )
        for question in assignment.questions:
            question.choices.sort(key=lambda choice: choice.choice_order)
    return assignment


def update_assignment(
    db: Session,
    assignment_id: UUID,
    assignment_data: AssignmentUpdate,
) -> Assignment | None:
    try:
        assignment = lock_assignment_for_update(db, assignment_id)
        if assignment is None:
            db.rollback()
            return None

        updates = assignment_data.model_dump(exclude_unset=True)
        if "pass_percentage" in updates:
            has_allocations = db.scalar(
                select(EmployeeAssignment.employee_assignment_id)
                .where(EmployeeAssignment.assignment_id == assignment_id)
                .limit(1)
            )
            if has_allocations is not None:
                raise ValueError(
                    "Passing percentage cannot be changed after allocation"
                )

        for field, value in updates.items():
            setattr(assignment, field, value)

        db.commit()
        db.refresh(assignment)
        return assignment
    except Exception:
        db.rollback()
        raise


def set_assignment_active(
    db: Session,
    assignment_id: UUID,
    is_active: bool,
) -> Assignment | None:
    try:
        assignment = lock_assignment_for_update(db, assignment_id)
        if assignment is None:
            db.rollback()
            return None

        assignment.is_active = is_active
        db.commit()
        db.refresh(assignment)
        return assignment
    except Exception:
        db.rollback()
        raise


def activate_assignment(db: Session, assignment_id: UUID) -> Assignment | None:
    return set_assignment_active(db, assignment_id, True)


def deactivate_assignment(db: Session, assignment_id: UUID) -> Assignment | None:
    return set_assignment_active(db, assignment_id, False)


def get_active_assignments_for_manager(db: Session) -> list[Assignment]:
    return get_active_assignments(db)


def get_active_assignments_for_employee(
    db: Session,
    employee: Employee,
) -> list[Assignment]:
    statement = (
        select(Assignment)
        .join(
            EmployeeAssignment,
            EmployeeAssignment.assignment_id == Assignment.assignment_id,
        )
        .where(
            EmployeeAssignment.employee_id == employee.employee_id,
            Assignment.is_active.is_(True),
        )
        .order_by(Assignment.title, Assignment.assignment_id)
    )
    return db.scalars(statement).unique().all()
