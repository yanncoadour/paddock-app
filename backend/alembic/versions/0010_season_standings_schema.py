"""season standings schema

Revision ID: 0010_season_standings_schema
Revises: 0009_gp_standings_schema
Create Date: 2024-01-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0010_season_standings_schema"
down_revision = "0009_gp_standings_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "season_standings",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("season_id", sa.BigInteger(), sa.ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paddock_id", sa.BigInteger(), sa.ForeignKey("paddocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("points_total", sa.Numeric(7, 1), nullable=False, server_default=sa.text("0")),
        sa.UniqueConstraint("season_id", "paddock_id", "user_id", name="uq_season_standings_season_paddock_user"),
    )
    op.create_index("ix_season_standings_season_id", "season_standings", ["season_id"])
    op.create_index("ix_season_standings_paddock_id", "season_standings", ["paddock_id"])
    op.create_index("ix_season_standings_user_id", "season_standings", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_season_standings_user_id", table_name="season_standings")
    op.drop_index("ix_season_standings_paddock_id", table_name="season_standings")
    op.drop_index("ix_season_standings_season_id", table_name="season_standings")
    op.drop_table("season_standings")
