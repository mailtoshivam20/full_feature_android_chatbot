"""fulltext index on messages.content

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-10

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE FULLTEXT INDEX idx_messages_content ON messages(content)")


def downgrade() -> None:
    op.execute("DROP INDEX idx_messages_content ON messages")
