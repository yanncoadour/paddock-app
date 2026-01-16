"""add beta whitelist

Revision ID: 0002_add_beta_whitelist
Revises: 0001_initial_schema
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0002_add_beta_whitelist"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "beta_whitelist_emails",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("email", name="uq_beta_whitelist_email"),
    )


def downgrade() -> None:
    op.drop_table("beta_whitelist_emails")
