"""update paddocks schema

Revision ID: 0003_update_paddocks_schema
Revises: 0002_add_beta_whitelist
Create Date: 2024-01-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0003_update_paddocks_schema"
down_revision = "0002_add_beta_whitelist"
branch_labels = None
depends_on = None


PADDOK_STATUS = "status IN ('draft', 'open', 'locked', 'finished')"
ROLE_STATUS = "role IN ('owner', 'member')"


def upgrade() -> None:
    with op.batch_alter_table("paddocks") as batch_op:
        batch_op.add_column(sa.Column("join_code", sa.String(length=16), nullable=True))
        batch_op.add_column(sa.Column("season_year", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("status", sa.String(length=16), nullable=True))
        batch_op.drop_column("invite_code")
        batch_op.drop_column("is_private")
        batch_op.drop_column("locked")

    op.execute("UPDATE paddocks SET join_code = concat('JOIN', id::text)")
    op.execute("UPDATE paddocks SET season_year = extract(year from created_at)::int")
    op.execute("UPDATE paddocks SET status = 'draft'")

    with op.batch_alter_table("paddocks") as batch_op:
        batch_op.alter_column("join_code", nullable=False)
        batch_op.alter_column("season_year", nullable=False)
        batch_op.alter_column("status", nullable=False)
        batch_op.create_unique_constraint("uq_paddocks_join_code", ["join_code"])
        batch_op.create_check_constraint("ck_paddocks_status", PADDOK_STATUS)

    op.drop_constraint("paddock_members_pkey", "paddock_members", type_="primary")
    op.drop_column("paddock_members", "id")
    op.create_primary_key("pk_paddock_members", "paddock_members", ["user_id", "paddock_id"])
    op.drop_constraint("uq_paddock_members_paddock_user", "paddock_members", type_="unique")
    op.create_check_constraint("ck_paddock_members_role", "paddock_members", ROLE_STATUS)


def downgrade() -> None:
    op.drop_constraint("ck_paddock_members_role", "paddock_members", type_="check")
    op.drop_constraint("pk_paddock_members", "paddock_members", type_="primary")
    op.add_column(
        "paddock_members",
        sa.Column("id", sa.BigInteger(), primary_key=True),
    )
    op.create_unique_constraint("uq_paddock_members_paddock_user", "paddock_members", ["paddock_id", "user_id"])
    op.create_primary_key("paddock_members_pkey", "paddock_members", ["id"])

    with op.batch_alter_table("paddocks") as batch_op:
        batch_op.drop_constraint("ck_paddocks_status", type_="check")
        batch_op.drop_constraint("uq_paddocks_join_code", type_="unique")
        batch_op.drop_column("join_code")
        batch_op.drop_column("season_year")
        batch_op.drop_column("status")
        batch_op.add_column(sa.Column("invite_code", sa.String(length=16), nullable=False))
        batch_op.add_column(sa.Column("is_private", sa.Boolean(), nullable=False, server_default=sa.text("true")))
        batch_op.add_column(sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.text("false")))
