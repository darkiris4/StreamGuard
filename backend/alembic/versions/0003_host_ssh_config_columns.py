"""add alias, port, identity_file, proxy_jump to host table

Revision ID: 0003_host_ssh_config_columns
Revises: 0002_host_ssh_fields
Create Date: 2026-02-08 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "0003_host_ssh_config_columns"
down_revision = "0002_host_ssh_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "host",
        sa.Column("alias", sa.String(), server_default="", nullable=False),
    )
    op.add_column(
        "host",
        sa.Column("port", sa.Integer(), server_default="22", nullable=False),
    )
    op.add_column(
        "host",
        sa.Column("identity_file", sa.String(), server_default="", nullable=False),
    )
    op.add_column(
        "host",
        sa.Column("proxy_jump", sa.String(), server_default="", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("host", "proxy_jump")
    op.drop_column("host", "identity_file")
    op.drop_column("host", "port")
    op.drop_column("host", "alias")
