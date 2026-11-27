from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.dependencies.authorization import employee_scope_filter
from app.models.assignment import Assignment
from app.models.assignment_question import AssignmentQuestion
from app.models.employee import Employee
from app.models.employee_assignment import EmployeeAssignment
from app.schemas.employee_assignment import (
    AssignmentAllocate,
    AssignmentStatus,
    EmployeeAssignedAssignmentResponse,
)
from app.services.assignment_question_service import (
    validate_assignment_readiness,
)
from app.services.assignment_service import lock_assignment_for_update


def allocate_assignment(
    db: Session,
    allocation: AssignmentAllocate,
    assigned_by: UUID,
) -> EmployeeAssignment:
    try:
        assignment = lock_assignment_for_update(db, allocation.assignment_id)
        if assignment is None:
            raise LookupError("Assignment not found")
        if not assignment.is_active:
            raise ValueError("Inactive assignments cannot be allocated")

        if db.get(Employee, allocation.employee_id) is None:
            raise LookupError("Employee not found")
        if db.get(Employee, assigned_by) is None:
            raise LookupError("Assigning employee not found")

        duplicate = db.scalar(
            select(EmployeeAssignment.employee_assignment_id)
            .where(
                EmployeeAssignment.employee_id == allocation.employee_id,
                EmployeeAssignment.assignment_id == allocation.assignment_id,
            )
            .limit(1)
        )
        if duplicate is not None:
            raise ValueError("Assignment is already allocated to this employee")

        validate_assignment_readiness(db, allocation.assignment_id)

        employee_assignment = EmployeeAssignment(
            employee_id=allocation.employee_id,
            assignment_id=allocation.assignment_id,
            assigned_by=assigned_by,
            status="assigned",
            score=None,
            result=None,
            submitted_at=None,
        )
        db.add(employee_assignment)
        db.commit()
        db.refresh(employee_assignment)
        return employee_assignment
    except IntegrityError as error:
        db.rollback()
        raise ValueError(
            "Assignment is already allocated or allocation references are invalid"
        ) from error
    except Exception:
        db.rollback()
        raise


def get_all_allocations(
    db: Session,
    employee_id: UUID | None = None,
    assignment_id: UUID | None = None,
    status: AssignmentStatus | None = None,
) -> list[EmployeeAssignment]:
    statement = select(EmployeeAssignment).options(
        selectinload(EmployeeAssignment.employee),
        selectinload(EmployeeAssignment.assignment),
    )
    if employee_id is not None:
        statement = statement.where(
            EmployeeAssignment.employee_id == employee_id
        )
    if assignment_id is not None:
        statement = statement.where(
            EmployeeAssignment.assignment_id == assignment_id
        )
    if status is not None:
        if status not in ("assigned", "submitted"):
            raise ValueError("Invalid employee assignment status")
        statement = statement.where(EmployeeAssignment.status == status)

    return db.scalars(
        statement.order_by(EmployeeAssignment.assigned_at.desc())
    ).all()


def get_allocation_by_id(
    db: Session,
    employee_assignment_id: UUID,
) -> EmployeeAssignment | None:
    statement = (
        select(EmployeeAssignment)
        .where(
            EmployeeAssignment.employee_assignment_id
            == employee_assignment_id
        )
        .options(
            selectinload(EmployeeAssignment.employee),
            selectinload(EmployeeAssignment.assignment),
        )
    )
    return db.scalar(statement)


def get_allocations_for_employee(
    db: Session,
    employee_id: UUID,
) -> list[EmployeeAssignment]:
    if db.get(Employee, employee_id) is None:
        raise LookupError("Employee not found")
    return get_all_allocations(db, employee_id=employee_id)


def get_allocations_for_assignment(
    db: Session,
    assignment_id: UUID,
) -> list[EmployeeAssignment]:
    if db.get(Assignment, assignment_id) is None:
        raise LookupError("Assignment not found")
    return get_all_allocations(db, assignment_id=assignment_id)


def get_manager_allocations(
    db: Session,
    manager: Employee,
    employee_id: UUID | None = None,
    assignment_id: UUID | None = None,
    status: AssignmentStatus | None = None,
) -> list[EmployeeAssignment]:
    scoped_employee_ids = select(Employee.employee_id).where(
        employee_scope_filter(db, manager)
    )
    statement = (
        select(EmployeeAssignment)
        .where(EmployeeAssignment.employee_id.in_(scoped_employee_ids))
        .options(
            selectinload(EmployeeAssignment.employee),
            selectinload(EmployeeAssignment.assignment),
        )
    )
    if employee_id is not None:
        statement = statement.where(
            EmployeeAssignment.employee_id == employee_id
        )
    if assignment_id is not None:
        statement = statement.where(
            EmployeeAssignment.assignment_id == assignment_id
        )
    if status is not None:
        if status not in ("assigned", "submitted"):
            raise ValueError("Invalid employee assignment status")
        statement = statement.where(EmployeeAssignment.status == status)

    return db.scalars(
        statement.order_by(EmployeeAssignment.assigned_at.desc())
    ).all()


def get_manager_allocation_by_id(
    db: Session,
    manager: Employee,
    employee_assignment_id: UUID,
) -> EmployeeAssignment | None:
    scoped_employee_ids = select(Employee.employee_id).where(
        employee_scope_filter(db, manager)
    )
    statement = (
        select(EmployeeAssignment)
        .where(
            EmployeeAssignment.employee_assignment_id
            == employee_assignment_id,
            EmployeeAssignment.employee_id.in_(scoped_employee_ids),
        )
        .options(
            selectinload(EmployeeAssignment.employee),
            selectinload(EmployeeAssignment.assignment),
        )
    )
    return db.scalar(statement)


def _sort_assignment_content(allocation: EmployeeAssignment) -> None:
    questions = allocation.assignment.questions
    questions.sort(
        key=lambda question: (question.question_order, question.question_id)
    )
    for question in questions:
        question.choices.sort(key=lambda choice: choice.choice_order)


def get_own_assignments(
    db: Session,
    employee: Employee,
) -> list[EmployeeAssignedAssignmentResponse]:
    statement = (
        select(EmployeeAssignment)
        .where(EmployeeAssignment.employee_id == employee.employee_id)
        .options(
            selectinload(EmployeeAssignment.assignment)
            .selectinload(Assignment.questions)
            .selectinload(AssignmentQuestion.choices)
        )
        .order_by(EmployeeAssignment.assigned_at.desc())
    )
    allocations = db.scalars(statement).all()
    for allocation in allocations:
        _sort_assignment_content(allocation)
    return [
        EmployeeAssignedAssignmentResponse.model_validate(allocation)
        for allocation in allocations
    ]


def get_own_assignment_detail(
    db: Session,
    employee: Employee,
    employee_assignment_id: UUID,
) -> EmployeeAssignedAssignmentResponse | None:
    statement = (
        select(EmployeeAssignment)
        .where(
            EmployeeAssignment.employee_assignment_id == employee_assignment_id,
            EmployeeAssignment.employee_id == employee.employee_id,
        )
        .options(
            selectinload(EmployeeAssignment.assignment)
            .selectinload(Assignment.questions)
            .selectinload(AssignmentQuestion.choices)
        )
    )
    allocation = db.scalar(statement)
    if allocation is None:
        return None
    _sort_assignment_content(allocation)
    return EmployeeAssignedAssignmentResponse.model_validate(allocation)
