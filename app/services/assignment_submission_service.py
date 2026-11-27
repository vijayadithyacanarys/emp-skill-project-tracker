from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db_compat import current_timestamp_expression
from app.models.assignment import Assignment
from app.models.assignment_question import AssignmentQuestion
from app.models.employee import Employee
from app.models.employee_assignment import EmployeeAssignment
from app.models.question_choice import QuestionChoice
from app.schemas.assignment_question import EmployeeQuestionResponse
from app.schemas.employee_assignment import (
    AssignmentResultResponse,
    AssignmentSubmission,
)


def _load_allocation_for_employee(
    db: Session,
    employee: Employee,
    employee_assignment_id: UUID,
    lock: bool = False,
) -> EmployeeAssignment | None:
    statement = select(EmployeeAssignment).where(
        EmployeeAssignment.employee_assignment_id == employee_assignment_id,
        EmployeeAssignment.employee_id == employee.employee_id,
    )
    if lock:
        statement = statement.with_for_update().with_hint(
            EmployeeAssignment,
            "WITH (UPDLOCK, ROWLOCK)",
            dialect_name="mssql",
        )
    return db.scalar(statement)


def get_assignment_questions_for_employee(
    db: Session,
    employee: Employee,
    employee_assignment_id: UUID,
) -> list[EmployeeQuestionResponse]:
    allocation = _load_allocation_for_employee(
        db,
        employee,
        employee_assignment_id,
    )
    if allocation is None:
        raise LookupError("Assignment allocation not found")
    if allocation.status != "assigned":
        raise ValueError("Assignment has already been submitted")

    statement = (
        select(AssignmentQuestion)
        .where(
            AssignmentQuestion.assignment_id == allocation.assignment_id
        )
        .options(selectinload(AssignmentQuestion.choices))
        .order_by(
            AssignmentQuestion.question_order,
            AssignmentQuestion.question_id,
        )
    )
    questions = db.scalars(statement).all()
    responses = []
    for question in questions:
        question.choices.sort(key=lambda choice: choice.choice_order)
        responses.append(EmployeeQuestionResponse.model_validate(question))
    return responses


def submit_assignment(
    db: Session,
    employee: Employee,
    employee_assignment_id: UUID,
    submission: AssignmentSubmission,
) -> AssignmentResultResponse:
    try:
        allocation = _load_allocation_for_employee(
            db,
            employee,
            employee_assignment_id,
            lock=True,
        )
        if allocation is None:
            raise LookupError("Assignment allocation not found")
        if allocation.status != "assigned":
            raise ValueError("Assignment has already been submitted")

        statement = (
            select(Assignment)
            .where(Assignment.assignment_id == allocation.assignment_id)
            .options(
                selectinload(Assignment.questions).selectinload(
                    AssignmentQuestion.choices
                )
            )
        )
        assignment = db.scalar(statement)
        if assignment is None:
            raise LookupError("Assignment not found")

        questions = sorted(
            assignment.questions,
            key=lambda question: (question.question_order, question.question_id),
        )
        if not questions:
            raise ValueError("Assignment has no questions")
        question_orders = [question.question_order for question in questions]
        if (
            any(order <= 0 for order in question_orders)
            or len(set(question_orders)) != len(question_orders)
        ):
            raise ValueError("Assignment question ordering is invalid")

        answers = submission.answers
        question_ids = {question.question_id for question in questions}
        if set(answers) != question_ids:
            raise ValueError(
                "Exactly one answer is required for every assignment question"
            )
        if len(set(answers.values())) != len(answers):
            raise ValueError("A choice cannot be selected more than once")

        choices_by_question: dict[UUID, dict[UUID, QuestionChoice]] = {}
        for question in questions:
            choices_by_question[question.question_id] = {
                choice.choice_id: choice for choice in question.choices
            }

        marks_obtained = 0
        total_marks = 0
        for question in questions:
            if question.marks <= 0 or len(question.choices) != 4:
                raise ValueError("Assignment question data is invalid")
            if (
                {choice.choice_order for choice in question.choices}
                != {1, 2, 3, 4}
            ):
                raise ValueError("Assignment question data is invalid")
            correct_choices = [
                choice for choice in question.choices if choice.is_correct
            ]
            if len(correct_choices) != 1:
                raise ValueError("Assignment question data is invalid")

            total_marks += question.marks
            selected_choice = choices_by_question[
                question.question_id
            ].get(answers[question.question_id])
            if selected_choice is None:
                raise ValueError(
                    "Selected choice does not belong to its question"
                )
            if selected_choice.is_correct:
                marks_obtained += question.marks

        if total_marks <= 0:
            raise ValueError("Assignment total marks must be positive")

        score = (
            Decimal(marks_obtained)
            * Decimal(100)
            / Decimal(total_marks)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        result = (
            "passed"
            if score >= Decimal(assignment.pass_percentage)
            else "failed"
        )

        allocation.score = score
        allocation.result = result
        allocation.status = "submitted"
        allocation.submitted_at = current_timestamp_expression()

        db.commit()
        db.refresh(allocation)
        return AssignmentResultResponse.model_validate(allocation)
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Unable to submit this assignment") from error
    except Exception:
        db.rollback()
        raise


def get_assignment_result_for_employee(
    db: Session,
    employee: Employee,
    employee_assignment_id: UUID,
) -> AssignmentResultResponse | None:
    allocation = _load_allocation_for_employee(
        db,
        employee,
        employee_assignment_id,
    )
    if allocation is None or allocation.status != "submitted":
        return None
    return AssignmentResultResponse.model_validate(allocation)
