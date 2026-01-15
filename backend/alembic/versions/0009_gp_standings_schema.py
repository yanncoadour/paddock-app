"""gp standings schema

Revision ID: 0009_gp_standings_schema
Revises: 0008_scores_schema_update
Create Date: 2024-01-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0009_gp_standings_schema"
down_revision = "0008_scores_schema_update"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gp_standings",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("gp_id", sa.BigInteger(), sa.ForeignKey("grand_prix.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("points", sa.Numeric(5, 1), nullable=False, server_default=sa.text("0")),
        sa.UniqueConstraint("gp_id", "user_id", name="uq_gp_standings_gp_user"),
    )
    op.create_index("ix_gp_standings_gp_id", "gp_standings", ["gp_id"])
    op.create_index("ix_gp_standings_user_id", "gp_standings", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_gp_standings_user_id", table_name="gp_standings")
    op.drop_index("ix_gp_standings_gp_id", table_name="gp_standings")
    op.drop_table("gp_standings")
