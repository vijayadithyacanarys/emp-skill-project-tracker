from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app.dependencies.authorization import employee_scope_filter
from app.models.assignment import Assignment
from app.models.employee import Employee
from app.models.employee_assignment import EmployeeAssignment
from app.schemas.assignment_report import (
    ManagerAssignmentReportResponse,
    ManagerEmployeeAssignmentResponse,
)
from app.schemas.employee_assignment import AssignmentStatus


def _validate_status(status: AssignmentStatus | None) -> None:
    if status is not None and status not in ("assigned", "submitted"):
        raise ValueError("Invalid employee assignment status")


def _filtered_results_statement(
    employee_id: UUID | None = None,
    assignment_id: UUID | None = None,
    status: AssignmentStatus | None = None,
):
    _validate_status(status)
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
        statement = statement.where(EmployeeAssignment.status == status)
    return statement.order_by(
        EmployeeAssignment.assigned_at.desc(),
        EmployeeAssignment.employee_assignment_id,
    )


def get_all_employee_assignment_results(
    db: Session,
    employee_id: UUID | None = None,
    assignment_id: UUID | None = None,
    status: AssignmentStatus | None = None,
) -> list[EmployeeAssignment]:
    return db.scalars(
        _filtered_results_statement(employee_id, assignment_id, status)
    ).all()


def get_employee_assignment_result(
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


def _assignment_counts_statement():
    return select(
        Assignment.assignment_id.label("assignment_id"),
        Assignment.title.label("title"),
        func.count(
            EmployeeAssignment.employee_assignment_id
        ).label("total_count"),
        func.coalesce(
            func.sum(
                case(
                    (EmployeeAssignment.status == "assigned", 1),
                    else_=0,
                )
            ),
            0,
        ).label("assigned_count"),
        func.coalesce(
            func.sum(
                case(
                    (EmployeeAssignment.status == "submitted", 1),
                    else_=0,
                )
            ),
            0,
        ).label("submitted_count"),
        func.coalesce(
            func.sum(
                case(
                    (EmployeeAssignment.result == "passed", 1),
                    else_=0,
                )
            ),
            0,
        ).label("passed_count"),
        func.coalesce(
            func.sum(
                case(
                    (EmployeeAssignment.result == "failed", 1),
                    else_=0,
                )
            ),
            0,
        ).label("failed_count"),
    ).outerjoin(
        EmployeeAssignment,
        EmployeeAssignment.assignment_id == Assignment.assignment_id,
    ).group_by(
        Assignment.assignment_id,
        Assignment.title,
    )


def get_assignment_result_summaries(
    db: Session,
    assignment_id: UUID | None = None,
) -> list[dict[str, object]]:
    statement = _assignment_counts_statement()
    if assignment_id is not None:
        statement = statement.where(Assignment.assignment_id == assignment_id)

    return [
        dict(row._mapping)
        for row in db.execute(
            statement.order_by(Assignment.title, Assignment.assignment_id)
        )
    ]


def get_assignment_result_summary(
    db: Session,
    assignment_id: UUID,
) -> dict[str, object] | None:
    summaries = get_assignment_result_summaries(db, assignment_id)
    return summaries[0] if summaries else None


def _manager_scoped_statement(
    db: Session,
    manager: Employee,
    employee_id: UUID | None = None,
    assignment_id: UUID | None = None,
    status: AssignmentStatus | None = None,
):
    _validate_status(status)
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
        statement = statement.where(EmployeeAssignment.status == status)
    return statement.order_by(
        EmployeeAssignment.assignment_id,
        EmployeeAssignment.assigned_at.desc(),
        EmployeeAssignment.employee_assignment_id,
    )


def _manager_reports_from_rows(
    allocations: list[EmployeeAssignment],
) -> list[ManagerAssignmentReportResponse]:
    grouped: dict[UUID, list[EmployeeAssignment]] = {}
    for allocation in allocations:
        grouped.setdefault(allocation.assignment_id, []).append(allocation)

    reports = []
    for assignment_id, items in grouped.items():
        assignment = items[0].assignment
        reports.append(
            ManagerAssignmentReportResponse(
                assignment_id=assignment_id,
                title=assignment.title,
                employee_assignments=[
                    ManagerEmployeeAssignmentResponse.model_validate(item)
                    for item in items
                ],
            )
        )
    reports.sort(key=lambda report: (report.title, report.assignment_id))
    return reports


def get_manager_assignment_reports(
    db: Session,
    manager: Employee,
    employee_id: UUID | None = None,
    assignment_id: UUID | None = None,
    status: AssignmentStatus | None = None,
) -> list[ManagerAssignmentReportResponse]:
    allocations = db.scalars(
        _manager_scoped_statement(
            db,
            manager,
            employee_id=employee_id,
            assignment_id=assignment_id,
            status=status,
        )
    ).all()
    return _manager_reports_from_rows(allocations)


def get_manager_assignment_report(
    db: Session,
    manager: Employee,
    assignment_id: UUID,
    employee_id: UUID | None = None,
    status: AssignmentStatus | None = None,
) -> ManagerAssignmentReportResponse | None:
    reports = get_manager_assignment_reports(
        db,
        manager,
        employee_id=employee_id,
        assignment_id=assignment_id,
        status=status,
    )
    return reports[0] if reports else None


def get_manager_assignment_result_summaries(
    db: Session,
    manager: Employee,
    assignment_id: UUID | None = None,
    employee_id: UUID | None = None,
) -> list[dict[str, object]]:
    scoped_employee_ids = select(Employee.employee_id).where(
        employee_scope_filter(db, manager)
    )
    statement = (
        select(
            Assignment.assignment_id.label("assignment_id"),
            Assignment.title.label("title"),
            func.count(
                EmployeeAssignment.employee_assignment_id
            ).label("total_count"),
            func.coalesce(
                func.sum(
                    case(
                        (EmployeeAssignment.status == "assigned", 1),
                        else_=0,
                    )
                ),
                0,
            ).label("assigned_count"),
            func.coalesce(
                func.sum(
                    case(
                        (EmployeeAssignment.status == "submitted", 1),
                        else_=0,
                    )
                ),
                0,
            ).label("submitted_count"),
            func.coalesce(
                func.sum(
                    case(
                        (EmployeeAssignment.result == "passed", 1),
                        else_=0,
                    )
                ),
                0,
            ).label("passed_count"),
            func.coalesce(
                func.sum(
                    case(
                        (EmployeeAssignment.result == "failed", 1),
                        else_=0,
                    )
                ),
                0,
            ).label("failed_count"),
        )
        .join(
            EmployeeAssignment,
            EmployeeAssignment.assignment_id == Assignment.assignment_id,
        )
        .where(EmployeeAssignment.employee_id.in_(scoped_employee_ids))
        .group_by(Assignment.assignment_id, Assignment.title)
    )
    if assignment_id is not None:
        statement = statement.where(Assignment.assignment_id == assignment_id)
    if employee_id is not None:
        statement = statement.where(
            EmployeeAssignment.employee_id == employee_id
        )

    return [
        dict(row._mapping)
        for row in db.execute(
            statement.order_by(Assignment.title, Assignment.assignment_id)
        )
    ]
