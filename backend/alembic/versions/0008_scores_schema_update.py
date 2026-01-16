"""scores schema update

Revision ID: 0008_scores_schema_update
Revises: 0007_bonus_cards_schema_update
Create Date: 2024-01-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0008_scores_schema_update"
down_revision = "0007_bonus_cards_schema_update"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "session_results",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("session_id", sa.BigInteger(), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("positions", postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("session_id", name="uq_session_results_session"),
    )
    op.create_index("ix_session_results_session_id", "session_results", ["session_id"])

    op.create_table(
        "gp_scores",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("gp_id", sa.BigInteger(), sa.ForeignKey("grand_prix.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score_brut", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("calculated_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("gp_id", "user_id", name="uq_gp_scores_gp_user"),
    )
    op.create_index("ix_gp_scores_gp_id", "gp_scores", ["gp_id"])
    op.create_index("ix_gp_scores_user_id", "gp_scores", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_gp_scores_user_id", table_name="gp_scores")
    op.drop_index("ix_gp_scores_gp_id", table_name="gp_scores")
    op.drop_table("gp_scores")

    op.drop_index("ix_session_results_session_id", table_name="session_results")
    op.drop_table("session_results")
