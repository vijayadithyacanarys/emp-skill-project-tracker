import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_compat import unicode_text

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.question_choice import QuestionChoice


class AssignmentQuestion(Base):
    __tablename__ = "assignment_questions"

    __table_args__ = (
        CheckConstraint(
            "question_order > 0",
            name="check_assignment_question_order_positive",
        ),
        CheckConstraint(
            "marks > 0",
            name="check_assignment_question_marks_positive",
        ),
    )

    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assignments.assignment_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question_text: Mapped[str] = mapped_column(
        unicode_text(),
        nullable=False,
    )

    question_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    marks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    assignment: Mapped["Assignment"] = relationship(
        back_populates="questions",
    )

    choices: Mapped[list["QuestionChoice"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
