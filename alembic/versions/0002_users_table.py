"""create users table with uuid string pk

Revision ID: 0002_users
Revises: 0001
Create Date: 2025-11-16
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_users"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True, index=True),
        sa.Column("username", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )


def downgrade() -> None:
    op.drop_table("users")


