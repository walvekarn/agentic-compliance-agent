"""initial schema for audit_trail, entity_history, feedback_log

Revision ID: 0001
Revises: None
Create Date: 2025-11-16
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # audit_trail
    op.create_table(
        "audit_trail",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, index=True),
        sa.Column("agent_type", sa.String(length=100), nullable=False, index=True),
        sa.Column("task_description", sa.Text(), nullable=False),
        sa.Column("task_category", sa.String(length=100), nullable=True, index=True),
        sa.Column("entity_name", sa.String(length=255), nullable=True, index=True),
        sa.Column("entity_type", sa.String(length=100), nullable=True),
        sa.Column("decision_outcome", sa.String(length=50), nullable=False, index=True),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=50), nullable=True, index=True),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("reasoning_chain", sa.JSON(), nullable=False),
        sa.Column("risk_factors", sa.JSON(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("escalation_reason", sa.Text(), nullable=True),
        sa.Column("entity_context", sa.JSON(), nullable=True),
        sa.Column("task_context", sa.JSON(), nullable=True),
        sa.Column("meta_data", sa.JSON(), nullable=True),
    )

    # feedback_log
    op.create_table(
        "feedback_log",
        sa.Column("feedback_id", sa.Integer(), primary_key=True, index=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, index=True),
        sa.Column("entity_name", sa.String(length=255), nullable=True, index=True),
        sa.Column("task_description", sa.Text(), nullable=False),
        sa.Column("ai_decision", sa.String(length=50), nullable=False, index=True),
        sa.Column("human_decision", sa.String(length=50), nullable=False, index=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_agreement", sa.Integer(), nullable=False),
        sa.Column("audit_trail_id", sa.Integer(), nullable=True, index=True),
        sa.Column("meta_data", sa.JSON(), nullable=True),
    )

    # entity_history
    op.create_table(
        "entity_history",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("entity_name", sa.String(length=255), nullable=False, index=True),
        sa.Column("task_category", sa.String(length=100), nullable=False, index=True),
        sa.Column("decision", sa.String(length=50), nullable=False, index=True),
        sa.Column("risk_level", sa.String(length=50), nullable=True, index=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, index=True),
        sa.Column("task_description", sa.Text(), nullable=True),
        sa.Column("jurisdictions", sa.JSON(), nullable=True),
        sa.Column("meta_data", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("entity_history")
    op.drop_table("feedback_log")
    op.drop_table("audit_trail")


