"""add picks table

Revision ID: 0005_add_picks_table
Revises: 0004_calendar_schema
Create Date: 2024-01-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005_add_picks_table"
down_revision = "0004_calendar_schema"
branch_labels = None
depends_on = None


PICK_TYPE_CHECK = "type IN ('TOP10', 'TOP8')"


def upgrade() -> None:
    op.create_table(
        "picks",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paddock_id", sa.BigInteger(), sa.ForeignKey("paddocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.BigInteger(), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("positions", postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column("submitted_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "session_id", name="uq_picks_user_session"),
    )
    op.create_check_constraint("ck_picks_type", "picks", PICK_TYPE_CHECK)
    op.create_index("ix_picks_user_id", "picks", ["user_id"])
    op.create_index("ix_picks_paddock_id", "picks", ["paddock_id"])
    op.create_index("ix_picks_session_id", "picks", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_picks_session_id", table_name="picks")
    op.drop_index("ix_picks_paddock_id", table_name="picks")
    op.drop_index("ix_picks_user_id", table_name="picks")
    op.drop_constraint("ck_picks_type", "picks", type_="check")
    op.drop_table("picks")
