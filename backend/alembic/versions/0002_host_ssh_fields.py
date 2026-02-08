"""add ssh_key_path and source to host table

Revision ID: 0002_host_ssh_fields
Revises: 0001_initial
Create Date: 2026-02-08 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_host_ssh_fields"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "host",
        sa.Column("ssh_key_path", sa.String(), server_default="", nullable=False),
    )
    op.add_column(
        "host",
        sa.Column("source", sa.String(), server_default="manual", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("host", "source")
    op.drop_column("host", "ssh_key_path")
