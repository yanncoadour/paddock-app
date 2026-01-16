"""bonus cards schema update

Revision ID: 0007_bonus_cards_schema_update
Revises: 0006_quiz_schema_update
Create Date: 2024-01-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0007_bonus_cards_schema_update"
down_revision = "0006_quiz_schema_update"
branch_labels = None
depends_on = None


CARD_TYPE_CHECK = "type IN ('BONUS', 'MALUS')"
SESSION_TYPE_CHECK = "session_type = 'RACE'"


def upgrade() -> None:
    with op.batch_alter_table("bonus_cards") as batch_op:
        batch_op.add_column(sa.Column("type", sa.String(length=10), nullable=True))

    op.execute("UPDATE bonus_cards SET type = CASE WHEN is_bonus THEN 'BONUS' ELSE 'MALUS' END")

    with op.batch_alter_table("bonus_cards") as batch_op:
        batch_op.alter_column("type", nullable=False)
        batch_op.create_check_constraint("ck_bonus_cards_type", CARD_TYPE_CHECK)
        batch_op.drop_column("is_bonus")

    with op.batch_alter_table("bonus_uses") as batch_op:
        batch_op.add_column(sa.Column("used_at_utc", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("season_half", sa.Integer(), nullable=True, server_default=sa.text("1")))
        batch_op.alter_column("session_type", existing_type=sa.String(length=30), nullable=False)
        batch_op.drop_column("value")
        batch_op.drop_column("created_at")

    op.execute("UPDATE bonus_uses SET used_at_utc = now()")
    op.execute("UPDATE bonus_uses SET season_half = 1")
    op.execute("UPDATE bonus_uses SET session_type = 'RACE'")

    with op.batch_alter_table("bonus_uses") as batch_op:
        batch_op.alter_column("used_at_utc", nullable=False)
        batch_op.alter_column("season_half", nullable=False)
        batch_op.create_check_constraint("ck_bonus_uses_session_type", SESSION_TYPE_CHECK)
        batch_op.create_unique_constraint(
            "uq_bonus_uses_card_player_gp",
            ["card_id", "played_by_user_id", "gp_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("bonus_uses") as batch_op:
        batch_op.drop_constraint("uq_bonus_uses_card_player_gp", type_="unique")
        batch_op.drop_constraint("ck_bonus_uses_session_type", type_="check")
        batch_op.add_column(sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")))
        batch_op.add_column(sa.Column("value", sa.Integer(), nullable=False, server_default=sa.text("0")))
        batch_op.drop_column("used_at_utc")
        batch_op.drop_column("season_half")

    with op.batch_alter_table("bonus_cards") as batch_op:
        batch_op.add_column(sa.Column("is_bonus", sa.Boolean(), nullable=False, server_default=sa.text("true")))
        batch_op.drop_constraint("ck_bonus_cards_type", type_="check")
        batch_op.drop_column("type")
