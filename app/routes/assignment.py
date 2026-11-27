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
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
)
from app.schemas.assignment_question import (
    EmployeeQuestionResponse,
    QuestionCreate,
    QuestionResponse,
    QuestionUpdate,
)
from app.schemas.assignment_report import ManagerAssignmentReportResponse
from app.schemas.employee_assignment import (
    AssignmentAllocate,
    AssignmentResultResponse,
    AssignmentStatus,
    AssignmentSubmission,
    EmployeeAssignedAssignmentResponse,
    EmployeeAssignmentDetailResponse,
    EmployeeAssignmentResponse,
)
from app.schemas.question_choice import (
    ChoiceCreate,
    ChoiceResponse,
    ChoiceUpdate,
)
from app.services.assignment_allocation_service import (
    allocate_assignment,
    get_all_allocations,
    get_allocation_by_id,
    get_own_assignment_detail,
    get_own_assignments,
)
from app.services.assignment_question_service import (
    add_choice,
    add_question,
    delete_choice,
    delete_question,
    get_question_by_id,
    get_questions_for_assignment,
    update_choice,
    update_question,
)
from app.services.assignment_report_service import (
    get_all_employee_assignment_results,
    get_assignment_result_summaries,
    get_employee_assignment_result,
    get_manager_assignment_report,
    get_manager_assignment_reports,
    get_manager_assignment_result_summaries,
)
from app.services.assignment_service import (
    activate_assignment,
    create_assignment,
    deactivate_assignment,
    get_active_assignments_for_manager,
    get_all_assignments,
    get_assignment_by_id,
    update_assignment,
)
from app.services.assignment_submission_service import (
    get_assignment_questions_for_employee,
    get_assignment_result_for_employee,
    submit_assignment,
)


router = APIRouter(
    prefix="/assignments",
    tags=["Assignments"],
)


def _raise_service_error(error: LookupError | ValueError) -> NoReturn:
    if isinstance(error, LookupError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    message = str(error)
    lowered_message = message.lower()
    conflict_markers = (
        "already",
        "conflict",
        "after allocation",
        "inactive assignments cannot be allocated",
        "unable to submit",
    )
    error_status = (
        status.HTTP_409_CONFLICT
        if any(marker in lowered_message for marker in conflict_markers)
        else status.HTTP_400_BAD_REQUEST
    )
    raise HTTPException(
        status_code=error_status,
        detail=message,
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
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assignment_endpoint(
    assignment_data: AssignmentCreate,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("project_skill:manage")
    ),
) -> AssignmentResponse:
    return create_assignment(db, assignment_data)


@router.get(
    "/",
    response_model=list[AssignmentResponse],
)
def get_all_assignments_endpoint(
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("allocation:read")
    ),
) -> list[AssignmentResponse]:
    return get_all_assignments(db, is_active=is_active)


@router.get(
    "/active",
    response_model=list[AssignmentResponse],
)
def get_active_assignments_endpoint(
    db: Session = Depends(get_db),
    actor: Employee = Depends(require_permission("allocation:read")),
) -> list[AssignmentResponse]:
    _require_manager_or_admin(db, actor)
    return get_active_assignments_for_manager(db)


@router.get(
    "/my",
    response_model=list[EmployeeAssignedAssignmentResponse],
)
def get_my_assignments_endpoint(
    db: Session = Depends(get_db),
    employee: Employee = Depends(require_permission("allocation:read")),
) -> list[EmployeeAssignedAssignmentResponse]:
    return get_own_assignments(db, employee)


@router.get(
    "/my/{employee_assignment_id}/questions",
    response_model=list[EmployeeQuestionResponse],
)
def get_my_assignment_questions_endpoint(
    employee_assignment_id: UUID,
    db: Session = Depends(get_db),
    employee: Employee = Depends(require_permission("allocation:read")),
) -> list[EmployeeQuestionResponse]:
    try:
        return get_assignment_questions_for_employee(
            db,
            employee,
            employee_assignment_id,
        )
    except (LookupError, ValueError) as error:
        _raise_service_error(error)


@router.post(
    "/my/{employee_assignment_id}/submit",
    response_model=AssignmentResultResponse,
)
def submit_my_assignment_endpoint(
    employee_assignment_id: UUID,
    submission: AssignmentSubmission,
    db: Session = Depends(get_db),
    employee: Employee = Depends(require_permission("allocation:read")),
) -> AssignmentResultResponse:
    try:
        return submit_assignment(
            db,
            employee,
            employee_assignment_id,
            submission,
        )
    except (LookupError, ValueError) as error:
        _raise_service_error(error)


@router.get(
    "/my/{employee_assignment_id}/result",
    response_model=AssignmentResultResponse,
)
def get_my_assignment_result_endpoint(
    employee_assignment_id: UUID,
    db: Session = Depends(get_db),
    employee: Employee = Depends(require_permission("allocation:read")),
) -> AssignmentResultResponse:
    result = get_assignment_result_for_employee(
        db,
        employee,
        employee_assignment_id,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submitted assignment result not found",
        )
    return result


@router.get(
    "/my/{employee_assignment_id}",
    response_model=EmployeeAssignedAssignmentResponse,
)
def get_my_assignment_detail_endpoint(
    employee_assignment_id: UUID,
    db: Session = Depends(get_db),
    employee: Employee = Depends(require_permission("allocation:read")),
) -> EmployeeAssignedAssignmentResponse:
    allocation = get_own_assignment_detail(
        db,
        employee,
        employee_assignment_id,
    )
    if allocation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment allocation not found",
        )
    return allocation


@router.get(
    "/reports/summary",
    response_model=list[dict[str, object]],
)
def get_manager_assignment_summaries_endpoint(
    assignment_id: UUID | None = None,
    employee_id: UUID | None = None,
    db: Session = Depends(get_db),
    manager: Employee = Depends(require_permission("allocation:read")),
) -> list[dict[str, object]]:
    _require_manager_or_admin(db, manager)
    return get_manager_assignment_result_summaries(
        db,
        manager,
        assignment_id=assignment_id,
        employee_id=employee_id,
    )


@router.get(
    "/reports",
    response_model=list[ManagerAssignmentReportResponse],
)
def get_manager_assignment_reports_endpoint(
    employee_id: UUID | None = None,
    assignment_id: UUID | None = None,
    report_status: AssignmentStatus | None = None,
    db: Session = Depends(get_db),
    manager: Employee = Depends(require_permission("allocation:read")),
) -> list[ManagerAssignmentReportResponse]:
    _require_manager_or_admin(db, manager)
    try:
        return get_manager_assignment_reports(
            db,
            manager,
            employee_id=employee_id,
            assignment_id=assignment_id,
            status=report_status,
        )
    except ValueError as error:
        _raise_service_error(error)


@router.get(
    "/reports/{assignment_id}",
    response_model=ManagerAssignmentReportResponse,
)
def get_manager_assignment_report_endpoint(
    assignment_id: UUID,
    employee_id: UUID | None = None,
    report_status: AssignmentStatus | None = None,
    db: Session = Depends(get_db),
    manager: Employee = Depends(require_permission("allocation:read")),
) -> ManagerAssignmentReportResponse:
    _require_manager_or_admin(db, manager)
    try:
        report = get_manager_assignment_report(
            db,
            manager,
            assignment_id,
            employee_id=employee_id,
            status=report_status,
        )
    except ValueError as error:
        _raise_service_error(error)

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment report not found",
        )
    return report


@router.get(
    "/results/summary",
    response_model=list[dict[str, object]],
)
def get_admin_assignment_summaries_endpoint(
    assignment_id: UUID | None = None,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("allocation:read")
    ),
) -> list[dict[str, object]]:
    return get_assignment_result_summaries(
        db,
        assignment_id=assignment_id,
    )


@router.get(
    "/results",
    response_model=list[EmployeeAssignmentResponse],
)
def get_admin_assignment_results_endpoint(
    employee_id: UUID | None = None,
    assignment_id: UUID | None = None,
    result_status: AssignmentStatus | None = None,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("allocation:read")
    ),
) -> list[EmployeeAssignmentResponse]:
    return get_all_employee_assignment_results(
        db,
        employee_id=employee_id,
        assignment_id=assignment_id,
        status=result_status,
    )


@router.get(
    "/results/{employee_assignment_id}",
    response_model=EmployeeAssignmentResponse,
)
def get_admin_assignment_result_endpoint(
    employee_assignment_id: UUID,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("allocation:read")
    ),
) -> EmployeeAssignmentResponse:
    result = get_employee_assignment_result(db, employee_assignment_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment result not found",
        )
    return result


@router.get(
    "/allocations",
    response_model=list[EmployeeAssignmentResponse],
)
def get_admin_allocations_endpoint(
    employee_id: UUID | None = None,
    assignment_id: UUID | None = None,
    allocation_status: AssignmentStatus | None = None,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("allocation:read")
    ),
) -> list[EmployeeAssignmentResponse]:
    try:
        return get_all_allocations(
            db,
            employee_id=employee_id,
            assignment_id=assignment_id,
            status=allocation_status,
        )
    except ValueError as error:
        _raise_service_error(error)


@router.post(
    "/allocations",
    response_model=EmployeeAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def allocate_assignment_endpoint(
    allocation: AssignmentAllocate,
    db: Session = Depends(get_db),
    admin: Employee = Depends(
        require_admin_permission("allocation:create")
    ),
) -> EmployeeAssignmentResponse:
    try:
        return allocate_assignment(
            db,
            allocation,
            assigned_by=admin.employee_id,
        )
    except (LookupError, ValueError) as error:
        _raise_service_error(error)


@router.get(
    "/allocations/{employee_assignment_id}",
    response_model=EmployeeAssignmentDetailResponse,
)
def get_admin_allocation_detail_endpoint(
    employee_assignment_id: UUID,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("allocation:read")
    ),
) -> EmployeeAssignmentDetailResponse:
    allocation = get_allocation_by_id(db, employee_assignment_id)
    if allocation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment allocation not found",
        )
    return allocation


@router.get(
    "/{assignment_id}",
    response_model=AssignmentResponse,
)
def get_assignment_by_id_endpoint(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    actor: Employee = Depends(require_permission("allocation:read")),
) -> AssignmentResponse:
    _require_manager_or_admin(db, actor)
    assignment = get_assignment_by_id(db, assignment_id)
    if assignment is None or (
        not employee_has_role(db, actor.employee_id, "Admin")
        and not assignment.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )
    return assignment


@router.patch(
    "/{assignment_id}",
    response_model=AssignmentResponse,
)
def update_assignment_endpoint(
    assignment_id: UUID,
    assignment_data: AssignmentUpdate,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("project_skill:manage")
    ),
) -> AssignmentResponse:
    try:
        assignment = update_assignment(db, assignment_id, assignment_data)
    except ValueError as error:
        _raise_service_error(error)

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )
    return assignment


@router.post(
    "/{assignment_id}/activate",
    response_model=AssignmentResponse,
)
def activate_assignment_endpoint(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("project_skill:manage")
    ),
) -> AssignmentResponse:
    assignment = activate_assignment(db, assignment_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )
    return assignment


@router.post(
    "/{assignment_id}/deactivate",
    response_model=AssignmentResponse,
)
def deactivate_assignment_endpoint(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("project_skill:manage")
    ),
) -> AssignmentResponse:
    assignment = deactivate_assignment(db, assignment_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )
    return assignment


@router.get(
    "/{assignment_id}/questions",
    response_model=list[QuestionResponse],
)
def get_assignment_questions_endpoint(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("project_skill:read")
    ),
) -> list[QuestionResponse]:
    try:
        return get_questions_for_assignment(db, assignment_id)
    except LookupError as error:
        _raise_service_error(error)


@router.post(
    "/{assignment_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_assignment_question_endpoint(
    assignment_id: UUID,
    question_data: QuestionCreate,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("project_skill:manage")
    ),
) -> QuestionResponse:
    try:
        return add_question(db, assignment_id, question_data)
    except (LookupError, ValueError) as error:
        _raise_service_error(error)


@router.get(
    "/{assignment_id}/questions/{question_id}",
    response_model=QuestionResponse,
)
def get_assignment_question_endpoint(
    assignment_id: UUID,
    question_id: UUID,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("project_skill:read")
    ),
) -> QuestionResponse:
    try:
        question = get_question_by_id(db, assignment_id, question_id)
    except LookupError as error:
        _raise_service_error(error)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )
    return question


@router.patch(
    "/{assignment_id}/questions/{question_id}",
    response_model=QuestionResponse,
)
def update_assignment_question_endpoint(
    assignment_id: UUID,
    question_id: UUID,
    question_data: QuestionUpdate,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("project_skill:manage")
    ),
) -> QuestionResponse:
    try:
        question = update_question(
            db,
            assignment_id,
            question_id,
            question_data,
        )
    except (LookupError, ValueError) as error:
        _raise_service_error(error)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )
    return question


@router.delete(
    "/{assignment_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_assignment_question_endpoint(
    assignment_id: UUID,
    question_id: UUID,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("project_skill:manage")
    ),
) -> None:
    try:
        deleted = delete_question(db, assignment_id, question_id)
    except LookupError as error:
        _raise_service_error(error)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )


@router.post(
    "/{assignment_id}/questions/{question_id}/choices",
    response_model=ChoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_question_choice_endpoint(
    assignment_id: UUID,
    question_id: UUID,
    choice_data: ChoiceCreate,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("project_skill:manage")
    ),
) -> ChoiceResponse:
    try:
        return add_choice(db, assignment_id, question_id, choice_data)
    except (LookupError, ValueError) as error:
        _raise_service_error(error)


@router.patch(
    "/{assignment_id}/questions/{question_id}/choices/{choice_id}",
    response_model=ChoiceResponse,
)
def update_question_choice_endpoint(
    assignment_id: UUID,
    question_id: UUID,
    choice_id: UUID,
    choice_data: ChoiceUpdate,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("project_skill:manage")
    ),
) -> ChoiceResponse:
    try:
        choice = update_choice(
            db,
            assignment_id,
            question_id,
            choice_id,
            choice_data,
        )
    except (LookupError, ValueError) as error:
        _raise_service_error(error)
    if choice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Choice not found",
        )
    return choice


@router.delete(
    "/{assignment_id}/questions/{question_id}/choices/{choice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_question_choice_endpoint(
    assignment_id: UUID,
    question_id: UUID,
    choice_id: UUID,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("project_skill:manage")
    ),
) -> None:
    try:
        deleted = delete_choice(
            db,
            assignment_id,
            question_id,
            choice_id,
        )
    except LookupError as error:
        _raise_service_error(error)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Choice not found",
        )
