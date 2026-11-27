import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Uuid, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_compat import unicode_text

if TYPE_CHECKING:
    from app.models.assignment_question import AssignmentQuestion


class QuestionChoice(Base):
    __tablename__ = "question_choices"

    __table_args__ = (
        CheckConstraint(
            "choice_order > 0",
            name="check_question_choice_order_positive",
        ),
    )

    choice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assignment_questions.question_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    choice_text: Mapped[str] = mapped_column(
        unicode_text(),
        nullable=False,
    )

    choice_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )

    question: Mapped["AssignmentQuestion"] = relationship(
        back_populates="choices",
    )
