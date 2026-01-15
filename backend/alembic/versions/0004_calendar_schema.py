"""calendar schema update

Revision ID: 0004_calendar_schema
Revises: 0003_update_paddocks_schema
Create Date: 2024-01-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0004_calendar_schema"
down_revision = "0003_update_paddocks_schema"
branch_labels = None
depends_on = None


SESSION_TYPE_CHECK = "type IN ('SPRINT_QUALI', 'SPRINT_RACE', 'QUALI', 'RACE')"
SESSION_STATUS_CHECK = "status IN ('open', 'locked', 'results')"


def upgrade() -> None:
    with op.batch_alter_table("seasons") as batch_op:
        batch_op.add_column(sa.Column("timezone_display", sa.String(length=64), nullable=True))
        batch_op.drop_constraint("uq_seasons_year", type_="unique")
        batch_op.drop_column("starts_at")
        batch_op.drop_column("ends_at")
        batch_op.alter_column("year", existing_type=sa.Integer(), nullable=False)
        batch_op.create_unique_constraint("uq_seasons_year", ["year"])

    op.execute("UPDATE seasons SET timezone_display = 'Europe/Paris'")

    with op.batch_alter_table("seasons") as batch_op:
        batch_op.alter_column("timezone_display", nullable=False)

    with op.batch_alter_table("grand_prix") as batch_op:
        batch_op.drop_constraint("uq_grand_prix_season_name", type_="unique")
        batch_op.add_column(sa.Column("country", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("starts_at_utc", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("has_sprint", sa.Boolean(), nullable=True, server_default=sa.text("false")))
        batch_op.add_column(sa.Column("round_number", sa.Integer(), nullable=True))
        batch_op.drop_column("location")
        batch_op.drop_column("starts_at")
        batch_op.drop_column("is_sprint")

    op.execute("UPDATE grand_prix SET country = name")
    op.execute("UPDATE grand_prix SET starts_at_utc = created_at")
    op.execute("UPDATE grand_prix SET has_sprint = false")
    op.execute("UPDATE grand_prix SET round_number = 1")

    with op.batch_alter_table("grand_prix") as batch_op:
        batch_op.alter_column("country", nullable=False)
        batch_op.alter_column("starts_at_utc", nullable=False)
        batch_op.alter_column("has_sprint", nullable=False)
        batch_op.alter_column("round_number", nullable=False)
        batch_op.create_unique_constraint("uq_grand_prix_season_round", ["season_id", "round_number"])

    with op.batch_alter_table("sessions") as batch_op:
        batch_op.add_column(sa.Column("type", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("deadline_utc", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("status", sa.String(length=16), nullable=True))
        batch_op.drop_constraint("uq_sessions_gp_type", type_="unique")
        batch_op.drop_column("session_type")
        batch_op.drop_column("deadline_at")

    op.execute("UPDATE sessions SET type = 'QUALI'")
    op.execute("UPDATE sessions SET deadline_utc = created_at")
    op.execute("UPDATE sessions SET status = 'open'")

    with op.batch_alter_table("sessions") as batch_op:
        batch_op.alter_column("type", nullable=False)
        batch_op.alter_column("deadline_utc", nullable=False)
        batch_op.alter_column("status", nullable=False)
        batch_op.create_check_constraint("ck_sessions_type", SESSION_TYPE_CHECK)
        batch_op.create_check_constraint("ck_sessions_status", SESSION_STATUS_CHECK)
        batch_op.create_unique_constraint("uq_sessions_gp_type", ["gp_id", "type"])


def downgrade() -> None:
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.drop_constraint("ck_sessions_status", type_="check")
        batch_op.drop_constraint("ck_sessions_type", type_="check")
        batch_op.drop_constraint("uq_sessions_gp_type", type_="unique")
        batch_op.add_column(sa.Column("session_type", sa.String(length=30), nullable=False))
        batch_op.add_column(sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False))
        batch_op.drop_column("type")
        batch_op.drop_column("deadline_utc")
        batch_op.drop_column("status")
        batch_op.create_unique_constraint("uq_sessions_gp_type", ["gp_id", "session_type"])

    with op.batch_alter_table("grand_prix") as batch_op:
        batch_op.drop_constraint("uq_grand_prix_season_round", type_="unique")
        batch_op.add_column(sa.Column("location", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False))
        batch_op.add_column(sa.Column("is_sprint", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        batch_op.drop_column("country")
        batch_op.drop_column("starts_at_utc")
        batch_op.drop_column("has_sprint")
        batch_op.drop_column("round_number")
        batch_op.create_unique_constraint("uq_grand_prix_season_name", ["season_id", "name"])

    with op.batch_alter_table("seasons") as batch_op:
        batch_op.drop_constraint("uq_seasons_year", type_="unique")
        batch_op.add_column(sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False))
        batch_op.add_column(sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False))
        batch_op.drop_column("timezone_display")
        batch_op.create_unique_constraint("uq_seasons_year", ["year"])
