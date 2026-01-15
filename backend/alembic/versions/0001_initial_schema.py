"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("favorite_team", sa.String(length=80), nullable=True),
        sa.Column("favorite_color", sa.String(length=7), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "paddocks",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_private", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("invite_code", sa.String(length=16), nullable=False),
        sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("owner_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("invite_code", name="uq_paddocks_invite_code"),
    )
    op.create_index("ix_paddocks_owner_id", "paddocks", ["owner_id"])

    op.create_table(
        "paddock_members",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("paddock_id", sa.BigInteger(), sa.ForeignKey("paddocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default=sa.text("'member'")),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("paddock_id", "user_id", name="uq_paddock_members_paddock_user"),
    )
    op.create_index("ix_paddock_members_paddock_id", "paddock_members", ["paddock_id"])
    op.create_index("ix_paddock_members_user_id", "paddock_members", ["user_id"])

    op.create_table(
        "seasons",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("year", name="uq_seasons_year"),
    )

    op.create_table(
        "grand_prix",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("season_id", sa.BigInteger(), sa.ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_sprint", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("season_id", "name", name="uq_grand_prix_season_name"),
    )
    op.create_index("ix_grand_prix_season_id", "grand_prix", ["season_id"])

    op.create_table(
        "sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("gp_id", sa.BigInteger(), sa.ForeignKey("grand_prix.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_type", sa.String(length=30), nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("gp_id", "session_type", name="uq_sessions_gp_type"),
    )
    op.create_index("ix_sessions_gp_id", "sessions", ["gp_id"])

    op.create_table(
        "predictions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paddock_id", sa.BigInteger(), sa.ForeignKey("paddocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.BigInteger(), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("picks", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "paddock_id", "session_id", name="uq_predictions_user_paddock_session"),
    )
    op.create_index("ix_predictions_user_id", "predictions", ["user_id"])
    op.create_index("ix_predictions_paddock_id", "predictions", ["paddock_id"])
    op.create_index("ix_predictions_session_id", "predictions", ["session_id"])

    op.create_table(
        "quizzes",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("season_id", sa.BigInteger(), sa.ForeignKey("seasons.id", ondelete="CASCADE"), nullable=True),
        sa.Column("gp_id", sa.BigInteger(), sa.ForeignKey("grand_prix.id", ondelete="CASCADE"), nullable=True),
        sa.Column("quiz_type", sa.String(length=20), nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_quizzes_season_id", "quizzes", ["season_id"])
    op.create_index("ix_quizzes_gp_id", "quizzes", ["gp_id"])

    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("quiz_id", sa.BigInteger(), sa.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("choices", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("correct_choices", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_quiz_questions_quiz_id", "quiz_questions", ["quiz_id"])

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

    op.create_table(
        "bonus_cards",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("is_bonus", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("code", name="uq_bonus_cards_code"),
    )

    op.create_table(
        "bonus_uses",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("gp_id", sa.BigInteger(), sa.ForeignKey("grand_prix.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_type", sa.String(length=30), nullable=False),
        sa.Column("card_id", sa.BigInteger(), sa.ForeignKey("bonus_cards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("played_by_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_bonus_uses_gp_id", "bonus_uses", ["gp_id"])
    op.create_index("ix_bonus_uses_card_id", "bonus_uses", ["card_id"])
    op.create_index("ix_bonus_uses_played_by", "bonus_uses", ["played_by_user_id"])
    op.create_index("ix_bonus_uses_target", "bonus_uses", ["target_user_id"])

    op.create_table(
        "scores",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paddock_id", sa.BigInteger(), sa.ForeignKey("paddocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gp_id", sa.BigInteger(), sa.ForeignKey("grand_prix.id", ondelete="CASCADE"), nullable=False),
        sa.Column("total_brut", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_points", sa.Numeric(5, 1), nullable=False, server_default=sa.text("0")),
        sa.Column("breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "paddock_id", "gp_id", name="uq_scores_user_paddock_gp"),
    )
    op.create_index("ix_scores_user_id", "scores", ["user_id"])
    op.create_index("ix_scores_paddock_id", "scores", ["paddock_id"])
    op.create_index("ix_scores_gp_id", "scores", ["gp_id"])


def downgrade() -> None:
    op.drop_index("ix_scores_gp_id", table_name="scores")
    op.drop_index("ix_scores_paddock_id", table_name="scores")
    op.drop_index("ix_scores_user_id", table_name="scores")
    op.drop_table("scores")

    op.drop_index("ix_bonus_uses_target", table_name="bonus_uses")
    op.drop_index("ix_bonus_uses_played_by", table_name="bonus_uses")
    op.drop_index("ix_bonus_uses_card_id", table_name="bonus_uses")
    op.drop_index("ix_bonus_uses_gp_id", table_name="bonus_uses")
    op.drop_table("bonus_uses")

    op.drop_table("bonus_cards")

    op.drop_index("ix_quiz_answers_question_id", table_name="quiz_answers")
    op.drop_index("ix_quiz_answers_quiz_id", table_name="quiz_answers")
    op.drop_index("ix_quiz_answers_user_id", table_name="quiz_answers")
    op.drop_table("quiz_answers")

    op.drop_index("ix_quiz_questions_quiz_id", table_name="quiz_questions")
    op.drop_table("quiz_questions")

    op.drop_index("ix_quizzes_gp_id", table_name="quizzes")
    op.drop_index("ix_quizzes_season_id", table_name="quizzes")
    op.drop_table("quizzes")

    op.drop_index("ix_predictions_session_id", table_name="predictions")
    op.drop_index("ix_predictions_paddock_id", table_name="predictions")
    op.drop_index("ix_predictions_user_id", table_name="predictions")
    op.drop_table("predictions")

    op.drop_index("ix_sessions_gp_id", table_name="sessions")
    op.drop_table("sessions")

    op.drop_index("ix_grand_prix_season_id", table_name="grand_prix")
    op.drop_table("grand_prix")

    op.drop_table("seasons")

    op.drop_index("ix_paddock_members_user_id", table_name="paddock_members")
    op.drop_index("ix_paddock_members_paddock_id", table_name="paddock_members")
    op.drop_table("paddock_members")

    op.drop_index("ix_paddocks_owner_id", table_name="paddocks")
    op.drop_table("paddocks")

    op.drop_table("users")
