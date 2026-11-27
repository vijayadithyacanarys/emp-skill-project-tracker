from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.assignment import Assignment
from app.models.assignment_question import AssignmentQuestion
from app.models.employee_assignment import EmployeeAssignment
from app.models.question_choice import QuestionChoice
from app.schemas.assignment_question import QuestionCreate, QuestionUpdate
from app.schemas.question_choice import ChoiceCreate, ChoiceUpdate
from app.services.assignment_service import lock_assignment_for_update


def _ensure_assignment_is_unallocated(db: Session, assignment_id: UUID) -> None:
    allocation_id = db.scalar(
        select(EmployeeAssignment.employee_assignment_id)
        .where(EmployeeAssignment.assignment_id == assignment_id)
        .limit(1)
    )
    if allocation_id is not None:
        raise ValueError(
            "Assignment questions and choices cannot change after allocation"
        )


def _validate_choice_payload(choices: list[ChoiceCreate]) -> None:
    if len(choices) != 4:
        raise ValueError("A question must contain exactly four choices")
    if sum(choice.is_correct for choice in choices) != 1:
        raise ValueError("Exactly one choice must be correct")
    if {choice.choice_order for choice in choices} != {1, 2, 3, 4}:
        raise ValueError("Choice orders must contain each value from 1 to 4")
    if any(not choice.choice_text.strip() for choice in choices):
        raise ValueError("Choice text must not be empty")


def _validate_choice_records(choices: list[QuestionChoice]) -> None:
    if len(choices) != 4:
        raise ValueError("A question must contain exactly four choices")
    if sum(choice.is_correct for choice in choices) != 1:
        raise ValueError("Exactly one choice must be correct")
    if {choice.choice_order for choice in choices} != {1, 2, 3, 4}:
        raise ValueError("Choice orders must contain each value from 1 to 4")
    if any(not choice.choice_text.strip() for choice in choices):
        raise ValueError("Choice text must not be empty")


def _get_question(
    db: Session,
    assignment_id: UUID,
    question_id: UUID,
) -> AssignmentQuestion | None:
    statement = (
        select(AssignmentQuestion)
        .where(
            AssignmentQuestion.assignment_id == assignment_id,
            AssignmentQuestion.question_id == question_id,
        )
        .options(selectinload(AssignmentQuestion.choices))
    )
    return db.scalar(statement)


def get_questions_for_assignment(
    db: Session,
    assignment_id: UUID,
) -> list[AssignmentQuestion]:
    if db.get(Assignment, assignment_id) is None:
        raise LookupError("Assignment not found")

    statement = (
        select(AssignmentQuestion)
        .where(AssignmentQuestion.assignment_id == assignment_id)
        .options(selectinload(AssignmentQuestion.choices))
        .order_by(AssignmentQuestion.question_order, AssignmentQuestion.question_id)
    )
    questions = db.scalars(statement).all()
    for question in questions:
        question.choices.sort(key=lambda choice: choice.choice_order)
    return questions


def get_question_by_id(
    db: Session,
    assignment_id: UUID,
    question_id: UUID,
) -> AssignmentQuestion | None:
    question = _get_question(db, assignment_id, question_id)
    if question is not None:
        question.choices.sort(key=lambda choice: choice.choice_order)
    return question


def validate_assignment_readiness(db: Session, assignment_id: UUID) -> None:
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise LookupError("Assignment not found")

    questions = get_questions_for_assignment(db, assignment_id)
    if not questions:
        raise ValueError("Assignment must contain at least one question")

    question_orders = [question.question_order for question in questions]
    if any(order <= 0 for order in question_orders):
        raise ValueError("Question orders must be positive")
    if len(set(question_orders)) != len(question_orders):
        raise ValueError("Question orders must be unique within an assignment")

    for question in questions:
        if not question.question_text.strip():
            raise ValueError("Question text must not be empty")
        if question.marks <= 0:
            raise ValueError("Question marks must be positive")
        _validate_choice_records(question.choices)


def add_question(
    db: Session,
    assignment_id: UUID,
    question_data: QuestionCreate,
) -> AssignmentQuestion:
    try:
        assignment = lock_assignment_for_update(db, assignment_id)
        if assignment is None:
            raise LookupError("Assignment not found")
        if not assignment.is_active:
            raise ValueError("Questions can only be added to active assignments")
        _ensure_assignment_is_unallocated(db, assignment_id)
        _validate_choice_payload(question_data.choices)
        if not question_data.question_text.strip():
            raise ValueError("Question text must not be empty")
        if question_data.question_order <= 0 or question_data.marks <= 0:
            raise ValueError("Question order and marks must be positive")

        duplicate_order = db.scalar(
            select(AssignmentQuestion.question_id)
            .where(
                AssignmentQuestion.assignment_id == assignment_id,
                AssignmentQuestion.question_order == question_data.question_order,
            )
            .limit(1)
        )
        if duplicate_order is not None:
            raise ValueError("Question order already exists in this assignment")

        question = AssignmentQuestion(
            assignment_id=assignment_id,
            question_text=question_data.question_text,
            question_order=question_data.question_order,
            marks=question_data.marks,
            choices=[
                QuestionChoice(**choice.model_dump())
                for choice in question_data.choices
            ],
        )
        db.add(question)
        db.commit()
        saved_question = _get_question(db, assignment_id, question.question_id)
        if saved_question is None:
            raise RuntimeError("Question was not available after creation")
        return saved_question
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Question conflicts with existing assignment data") from error
    except Exception:
        db.rollback()
        raise


def update_question(
    db: Session,
    assignment_id: UUID,
    question_id: UUID,
    question_data: QuestionUpdate,
    choices: list[ChoiceCreate] | None = None,
) -> AssignmentQuestion | None:
    try:
        assignment = lock_assignment_for_update(db, assignment_id)
        if assignment is None:
            raise LookupError("Assignment not found")
        _ensure_assignment_is_unallocated(db, assignment_id)

        question = _get_question(db, assignment_id, question_id)
        if question is None:
            db.rollback()
            return None

        updates = question_data.model_dump(exclude_unset=True)
        if not updates:
            raise ValueError("At least one question field must be provided")
        if (
            "question_text" in updates
            and not updates["question_text"].strip()
        ):
            raise ValueError("Question text must not be empty")
        if (
            "question_order" in updates
            and updates["question_order"] <= 0
        ) or ("marks" in updates and updates["marks"] <= 0):
            raise ValueError("Question order and marks must be positive")

        new_order = updates.get("question_order", question.question_order)
        duplicate_order = db.scalar(
            select(AssignmentQuestion.question_id)
            .where(
                AssignmentQuestion.assignment_id == assignment_id,
                AssignmentQuestion.question_order == new_order,
                AssignmentQuestion.question_id != question_id,
            )
            .limit(1)
        )
        if duplicate_order is not None:
            raise ValueError(
                "Question order already exists in this assignment"
            )

        if choices is not None:
            _validate_choice_payload(choices)
        else:
            _validate_choice_records(question.choices)

        for field, value in updates.items():
            setattr(question, field, value)

        if choices is not None:
            question.choices.clear()
            db.flush()
            question.choices.extend(
                QuestionChoice(**choice.model_dump())
                for choice in choices
            )

        db.commit()
        updated_question = _get_question(db, assignment_id, question_id)
        if updated_question is None:
            raise RuntimeError("Question was not available after update")
        return updated_question
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Question conflicts with existing assignment data") from error
    except Exception:
        db.rollback()
        raise


def delete_question(
    db: Session,
    assignment_id: UUID,
    question_id: UUID,
) -> bool:
    try:
        assignment = lock_assignment_for_update(db, assignment_id)
        if assignment is None:
            raise LookupError("Assignment not found")
        _ensure_assignment_is_unallocated(db, assignment_id)

        question = _get_question(db, assignment_id, question_id)
        if question is None:
            db.rollback()
            return False

        db.delete(question)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def add_choice(
    db: Session,
    assignment_id: UUID,
    question_id: UUID,
    choice_data: ChoiceCreate,
) -> QuestionChoice:
    try:
        assignment = lock_assignment_for_update(db, assignment_id)
        if assignment is None:
            raise LookupError("Assignment not found")
        _ensure_assignment_is_unallocated(db, assignment_id)

        question = _get_question(db, assignment_id, question_id)
        if question is None:
            raise LookupError("Question not found for assignment")

        if not 1 <= choice_data.choice_order <= 4:
            raise ValueError("Choice order must be between 1 and 4")
        if not choice_data.choice_text.strip():
            raise ValueError("Choice text must not be empty")
        if len(question.choices) >= 4:
            raise ValueError("A question cannot contain more than four choices")
        if any(c.choice_order == choice_data.choice_order for c in question.choices):
            raise ValueError("Choice order already exists for this question")
        if choice_data.is_correct and any(c.is_correct for c in question.choices):
            raise ValueError("A question can have only one correct choice")

        choice = QuestionChoice(
            question_id=question_id,
            **choice_data.model_dump(),
        )
        db.add(choice)
        db.commit()
        return choice
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Choice conflicts with existing question data") from error
    except Exception:
        db.rollback()
        raise


def update_choice(
    db: Session,
    assignment_id: UUID,
    question_id: UUID,
    choice_id: UUID,
    choice_data: ChoiceUpdate,
) -> QuestionChoice | None:
    try:
        assignment = lock_assignment_for_update(db, assignment_id)
        if assignment is None:
            raise LookupError("Assignment not found")
        _ensure_assignment_is_unallocated(db, assignment_id)

        question = _get_question(db, assignment_id, question_id)
        if question is None:
            raise LookupError("Question not found for assignment")

        choice = next(
            (item for item in question.choices if item.choice_id == choice_id),
            None,
        )
        if choice is None:
            db.rollback()
            return None

        updates = choice_data.model_dump(exclude_unset=True)
        if not updates:
            raise ValueError("At least one choice field must be provided")
        if (
            "choice_text" in updates
            and not updates["choice_text"].strip()
        ):
            raise ValueError("Choice text must not be empty")
        if (
            "choice_order" in updates
            and not 1 <= updates["choice_order"] <= 4
        ):
            raise ValueError("Choice order must be between 1 and 4")

        resulting_orders = [
            updates.get("choice_order", item.choice_order)
            if item.choice_id == choice_id
            else item.choice_order
            for item in question.choices
        ]
        if len(set(resulting_orders)) != len(resulting_orders):
            raise ValueError("Choice order must be unique within a question")

        correct_count = sum(
            updates.get("is_correct", item.is_correct)
            if item.choice_id == choice_id
            else item.is_correct
            for item in question.choices
        )
        if (
            len(question.choices) == 4 and correct_count != 1
        ) or correct_count > 1:
            raise ValueError("A complete question must have exactly one correct choice")

        for field, value in updates.items():
            setattr(choice, field, value)

        db.commit()
        db.refresh(choice)
        return choice
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Choice conflicts with existing question data") from error
    except Exception:
        db.rollback()
        raise


def delete_choice(
    db: Session,
    assignment_id: UUID,
    question_id: UUID,
    choice_id: UUID,
) -> bool:
    try:
        assignment = lock_assignment_for_update(db, assignment_id)
        if assignment is None:
            raise LookupError("Assignment not found")
        _ensure_assignment_is_unallocated(db, assignment_id)

        question = _get_question(db, assignment_id, question_id)
        if question is None:
            raise LookupError("Question not found for assignment")
        choice = next(
            (item for item in question.choices if item.choice_id == choice_id),
            None,
        )
        if choice is None:
            db.rollback()
            return False

        db.delete(choice)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
