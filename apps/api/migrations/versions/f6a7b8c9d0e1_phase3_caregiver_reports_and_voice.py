"""phase3_caregiver_reports_and_voice

Revision ID: f6a7b8c9d0e1
Revises: d4e5f6a7b8c9
Create Date: 2026-09-19 23:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('caregiver_reports',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('patient_id', sa.Uuid(), nullable=False),
    sa.Column('recorded_by', sa.Uuid(), nullable=True),
    sa.Column('reported_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('mode', sa.String(length=32), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('pain_level', sa.Integer(), nullable=True),
    sa.Column('sleep_hours', sa.String(length=32), nullable=True),
    sa.Column('food_intake', sa.String(length=128), nullable=True),
    sa.Column('mobility', sa.String(length=128), nullable=True),
    sa.Column('mood', sa.String(length=128), nullable=True),
    sa.Column('breathing', sa.String(length=128), nullable=True),
    sa.Column('energy', sa.String(length=128), nullable=True),
    sa.Column('general_concern', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('transcript', sa.Text(), nullable=True),
    sa.Column('audio_duration_seconds', sa.Integer(), nullable=True),
    sa.Column('ai_generated', sa.Boolean(), nullable=False),
    sa.Column('provider', sa.String(length=64), nullable=True),
    sa.Column('model', sa.String(length=128), nullable=True),
    sa.Column('model_version', sa.String(length=64), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=True),
    sa.Column('extraction', sa.JSON(), nullable=True),
    sa.Column('human_verified', sa.Boolean(), nullable=False),
    sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('confirmed_by', sa.Uuid(), nullable=True),
    sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('cancelled_by', sa.Uuid(), nullable=True),
    sa.Column('cancellation_reason', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['recorded_by'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_caregiver_reports_organization_id'), 'caregiver_reports', ['organization_id'], unique=False)
    op.create_index(op.f('ix_caregiver_reports_patient_id'), 'caregiver_reports', ['patient_id'], unique=False)
    op.create_index(op.f('ix_caregiver_reports_reported_at'), 'caregiver_reports', ['reported_at'], unique=False)
    op.create_index(op.f('ix_caregiver_reports_status'), 'caregiver_reports', ['status'], unique=False)

    op.add_column('observations', sa.Column('source_reference', sa.Uuid(), nullable=True))
    op.add_column('observations', sa.Column('ai_generated', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('observations', sa.Column('human_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('observations', sa.Column('confidence', sa.Float(), nullable=True))
    op.add_column('observations', sa.Column('model_version', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_observations_source_reference'), 'observations', ['source_reference'], unique=False)
    op.create_foreign_key(
        'fk_observations_source_reference_caregiver_reports',
        'observations',
        'caregiver_reports',
        ['source_reference'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_observations_source_reference_caregiver_reports', 'observations', type_='foreignkey')
    op.drop_index(op.f('ix_observations_source_reference'), table_name='observations')
    op.drop_column('observations', 'model_version')
    op.drop_column('observations', 'confidence')
    op.drop_column('observations', 'human_verified')
    op.drop_column('observations', 'ai_generated')
    op.drop_column('observations', 'source_reference')

    op.drop_index(op.f('ix_caregiver_reports_status'), table_name='caregiver_reports')
    op.drop_index(op.f('ix_caregiver_reports_reported_at'), table_name='caregiver_reports')
    op.drop_index(op.f('ix_caregiver_reports_patient_id'), table_name='caregiver_reports')
    op.drop_index(op.f('ix_caregiver_reports_organization_id'), table_name='caregiver_reports')
    op.drop_table('caregiver_reports')