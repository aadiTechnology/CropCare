"""Initial crops, diseases, remedies, and diagnosis history tables.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crops",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name_en", sa.String(length=120), nullable=False),
        sa.Column("name_mr", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "diseases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("crop_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name_en", sa.String(length=160), nullable=False),
        sa.Column("name_mr", sa.String(length=160), nullable=False),
        sa.Column("symptoms_en", sa.Text(), nullable=True),
        sa.Column("symptoms_mr", sa.Text(), nullable=True),
        sa.Column("verification_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["crop_id"], ["crops.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "remedies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("disease_id", sa.Uuid(), nullable=False),
        sa.Column("remedy_en", sa.Text(), nullable=True),
        sa.Column("remedy_mr", sa.Text(), nullable=True),
        sa.Column("prevention_en", sa.Text(), nullable=True),
        sa.Column("prevention_mr", sa.Text(), nullable=True),
        sa.Column("verification_status", sa.String(length=32), nullable=False),
        sa.Column("verified_by", sa.String(length=160), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["disease_id"], ["diseases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "diagnosis_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("crop_id", sa.Uuid(), nullable=False),
        sa.Column("disease_id", sa.Uuid(), nullable=True),
        sa.Column("remedy_id", sa.Uuid(), nullable=True),
        sa.Column("predicted_class", sa.String(length=160), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("diagnosis_mode", sa.String(length=16), nullable=False),
        sa.Column("image_reference", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["crop_id"], ["crops.id"]),
        sa.ForeignKeyConstraint(["disease_id"], ["diseases.id"]),
        sa.ForeignKeyConstraint(["remedy_id"], ["remedies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("diagnosis_history")
    op.drop_table("remedies")
    op.drop_table("diseases")
    op.drop_table("crops")
