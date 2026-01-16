"""quiz schema update

Revision ID: 0006_quiz_schema_update
Revises: 0005_add_picks_table
Create Date: 2024-01-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006_quiz_schema_update"
down_revision = "0005_add_picks_table"
branch_labels = None
depends_on = None


QUIZ_SCOPE_CHECK = "scope IN ('PRESEASON', 'GP', 'SPRINT')"


def upgrade() -> None:
    with op.batch_alter_table("quizzes") as batch_op:
        batch_op.add_column(sa.Column("scope", sa.String(length=16), nullable=True))
        batch_op.add_column(sa.Column("title", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("is_open", sa.Boolean(), nullable=True, server_default=sa.text("true")))

    op.execute(
        """
        UPDATE quizzes
        SET scope = CASE
            WHEN quiz_type IN ('PRESEASON', 'GP', 'SPRINT') THEN quiz_type
            ELSE 'GP'
        END
        """
    )
    op.execute("UPDATE quizzes SET title = 'QCM'")
    op.execute("UPDATE quizzes SET is_open = true")

    with op.batch_alter_table("quizzes") as batch_op:
        batch_op.alter_column("scope", nullable=False)
        batch_op.alter_column("title", nullable=False)
        batch_op.alter_column("is_open", nullable=False)
        batch_op.create_check_constraint("ck_quizzes_scope", QUIZ_SCOPE_CHECK)
        batch_op.drop_column("quiz_type")
        batch_op.drop_column("deadline_at")

    with op.batch_alter_table("quiz_questions") as batch_op:
        batch_op.add_column(sa.Column("text", sa.Text(), nullable=True))

    op.execute("UPDATE quiz_questions SET text = prompt")

    with op.batch_alter_table("quiz_questions") as batch_op:
        batch_op.alter_column("text", nullable=False)
        batch_op.drop_column("prompt")
        batch_op.drop_column("choices")
        batch_op.drop_column("correct_choices")

    op.drop_table("quiz_answers")

    op.create_table(
        "quiz_answers",
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quiz_id", sa.BigInteger(), sa.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("choice_id", sa.String(length=64), nullable=False),
        sa.Column("submitted_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "quiz_id", "question_id", name="uq_quiz_answers_user_quiz_question"),
    )
    op.create_index("ix_quiz_answers_user_id", "quiz_answers", ["user_id"])
    op.create_index("ix_quiz_answers_quiz_id", "quiz_answers", ["quiz_id"])
    op.create_index("ix_quiz_answers_question_id", "quiz_answers", ["question_id"])

    op.create_table(
        "quiz_choices",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("choice_id", sa.String(length=64), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.UniqueConstraint("question_id", "choice_id", name="uq_quiz_choices_question_choice"),
    )
    op.create_index("ix_quiz_choices_question_id", "quiz_choices", ["question_id"])

    op.create_table(
        "quiz_correct_choices",
        sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("choice_id", sa.String(length=64), nullable=False),
        sa.UniqueConstraint("question_id", "choice_id", name="uq_quiz_correct_choices_question_choice"),
    )
    op.create_index("ix_quiz_correct_choices_question_id", "quiz_correct_choices", ["question_id"])


def downgrade() -> None:
    op.drop_index("ix_quiz_correct_choices_question_id", table_name="quiz_correct_choices")
    op.drop_table("quiz_correct_choices")

    op.drop_index("ix_quiz_choices_question_id", table_name="quiz_choices")
    op.drop_table("quiz_choices")

    op.drop_index("ix_quiz_answers_question_id", table_name="quiz_answers")
    op.drop_index("ix_quiz_answers_quiz_id", table_name="quiz_answers")
    op.drop_index("ix_quiz_answers_user_id", table_name="quiz_answers")
    op.drop_table("quiz_answers")

    op.create_table(
        "quiz_answers",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quiz_id", sa.BigInteger(), sa.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("choice_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "quiz_id", "question_id", name="uq_quiz_answers_user_quiz_question"),
    )
    op.create_index("ix_quiz_answers_user_id", "quiz_answers", ["user_id"])
    op.create_index("ix_quiz_answers_quiz_id", "quiz_answers", ["quiz_id"])
    op.create_index("ix_quiz_answers_question_id", "quiz_answers", ["question_id"])

    with op.batch_alter_table("quiz_questions") as batch_op:
        batch_op.add_column(sa.Column("prompt", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "choices",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "correct_choices",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            )
        )

    op.execute("UPDATE quiz_questions SET prompt = text")

    with op.batch_alter_table("quiz_questions") as batch_op:
        batch_op.alter_column("prompt", nullable=False)
        batch_op.drop_column("text")
        batch_op.drop_column("choices")
        batch_op.drop_column("correct_choices")

    with op.batch_alter_table("quizzes") as batch_op:
        batch_op.add_column(sa.Column("quiz_type", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE quizzes SET quiz_type = scope")
    op.execute("UPDATE quizzes SET deadline_at = created_at")

    with op.batch_alter_table("quizzes") as batch_op:
        batch_op.alter_column("quiz_type", nullable=False)
        batch_op.alter_column("deadline_at", nullable=False)
        batch_op.drop_constraint("ck_quizzes_scope", type_="check")
        batch_op.drop_column("scope")
        batch_op.drop_column("title")
        batch_op.drop_column("is_open")
