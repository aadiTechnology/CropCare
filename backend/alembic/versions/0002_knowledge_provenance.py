"""Add guidance provenance and verification checks.

Revision ID: 0002_knowledge_provenance
Revises: 0001_initial_schema
Create Date: 2026-10-15

Adds nullable citation and review columns. Does not insert catalog rows
and does not drop existing tables.

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_knowledge_provenance"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VERIFICATION_STATUS_CHECK = "verification_status IN ('sample', 'expert_verified')"
EXPERT_PROVENANCE_CHECK = (
    "verification_status <> 'expert_verified' OR ("
    "source IS NOT NULL AND length(trim(source)) > 0 AND "
    "verified_by IS NOT NULL AND length(trim(verified_by)) > 0 AND "
    "verified_at IS NOT NULL)"
)


def upgrade() -> None:
    with op.batch_alter_table("diseases") as batch:
        batch.add_column(sa.Column("source", sa.Text(), nullable=True))
        batch.add_column(sa.Column("verified_by", sa.String(length=160), nullable=True))
        batch.add_column(sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_check_constraint("ck_diseases_verification_status", VERIFICATION_STATUS_CHECK)
        batch.create_check_constraint("ck_diseases_expert_provenance", EXPERT_PROVENANCE_CHECK)
    with op.batch_alter_table("remedies") as batch:
        batch.add_column(sa.Column("source", sa.Text(), nullable=True))
        batch.create_check_constraint("ck_remedies_verification_status", VERIFICATION_STATUS_CHECK)
        batch.create_check_constraint("ck_remedies_expert_provenance", EXPERT_PROVENANCE_CHECK)


def downgrade() -> None:
    with op.batch_alter_table("remedies") as batch:
        batch.drop_constraint("ck_remedies_expert_provenance", type_="check")
        batch.drop_constraint("ck_remedies_verification_status", type_="check")
        batch.drop_column("source")
    with op.batch_alter_table("diseases") as batch:
        batch.drop_constraint("ck_diseases_expert_provenance", type_="check")
        batch.drop_constraint("ck_diseases_verification_status", type_="check")
        batch.drop_column("verified_at")
        batch.drop_column("verified_by")
        batch.drop_column("source")
