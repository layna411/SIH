"""step7_phase_c_aicte_cases_and_actions

Revision ID: d8c23e4f5a6b
Revises: c7b12d3e4f5a
Create Date: 2026-10-29 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8c23e4f5a6b'
down_revision: Union[str, Sequence[str], None] = 'c7b12d3e4f5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for Step 7 Phase C: AICTE Cases & Procedural Action History."""
    # 1. Create aicte_cases table
    op.create_table(
        'aicte_cases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('case_reference', sa.String(length=50), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('source_grievance_id', sa.Integer(), nullable=True),
        sa.Column('source_type', sa.String(length=50), server_default='DIRECT', nullable=False),
        sa.Column('official_reference_number', sa.String(length=100), nullable=True),
        sa.Column('received_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('complainant_type', sa.String(length=50), server_default='STAKEHOLDER', nullable=False),
        sa.Column('complainant_name', sa.String(length=255), nullable=True),
        sa.Column('complainant_email', sa.String(length=255), nullable=True),
        sa.Column('complainant_phone', sa.String(length=50), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='RECEIVED', nullable=False),
        sa.Column('current_unit_id', sa.Integer(), nullable=False),
        sa.Column('assigned_officer_id', sa.Integer(), nullable=True),
        sa.Column('region', sa.String(length=50), nullable=True),
        sa.Column('priority', sa.String(length=50), server_default='NORMAL', nullable=False),
        sa.Column('last_action_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('next_action_required', sa.String(length=255), nullable=True),
        sa.Column('next_action_due_at', sa.DateTime(), nullable=True),
        sa.Column('expected_disposal_at', sa.DateTime(), nullable=True),
        sa.Column('disposed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_officer_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['current_unit_id'], ['organizational_units.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_grievance_id'], ['grievances.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('case_reference', name='uq_aicte_cases_case_reference')
    )
    op.create_index(op.f('ix_aicte_cases_id'), 'aicte_cases', ['id'], unique=False)
    op.create_index(op.f('ix_aicte_cases_case_reference'), 'aicte_cases', ['case_reference'], unique=True)
    op.create_index(op.f('ix_aicte_cases_institution_id'), 'aicte_cases', ['institution_id'], unique=False)
    op.create_index(op.f('ix_aicte_cases_source_grievance_id'), 'aicte_cases', ['source_grievance_id'], unique=False)
    op.create_index(op.f('ix_aicte_cases_current_unit_id'), 'aicte_cases', ['current_unit_id'], unique=False)
    op.create_index(op.f('ix_aicte_cases_assigned_officer_id'), 'aicte_cases', ['assigned_officer_id'], unique=False)
    op.create_index(op.f('ix_aicte_cases_status'), 'aicte_cases', ['status'], unique=False)
    op.create_index(op.f('ix_aicte_cases_category'), 'aicte_cases', ['category'], unique=False)
    op.create_index(op.f('ix_aicte_cases_region'), 'aicte_cases', ['region'], unique=False)
    op.create_index(op.f('ix_aicte_cases_priority'), 'aicte_cases', ['priority'], unique=False)
    op.create_index(op.f('ix_aicte_cases_received_at'), 'aicte_cases', ['received_at'], unique=False)
    op.create_index(op.f('ix_aicte_cases_created_at'), 'aicte_cases', ['created_at'], unique=False)

    # 2. Create case_actions table
    op.create_table(
        'case_actions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('action_title', sa.String(length=255), nullable=False),
        sa.Column('action_description', sa.Text(), nullable=True),
        sa.Column('previous_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=True),
        sa.Column('unit_id', sa.Integer(), nullable=False),
        sa.Column('performed_by_user_id', sa.Integer(), nullable=False),
        sa.Column('action_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('supporting_document_ref', sa.String(length=255), nullable=True),
        sa.Column('next_action_required', sa.String(length=255), nullable=True),
        sa.Column('next_action_due_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['aicte_cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['unit_id'], ['organizational_units.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_case_actions_id'), 'case_actions', ['id'], unique=False)
    op.create_index(op.f('ix_case_actions_case_id'), 'case_actions', ['case_id'], unique=False)
    op.create_index(op.f('ix_case_actions_action_type'), 'case_actions', ['action_type'], unique=False)
    op.create_index(op.f('ix_case_actions_unit_id'), 'case_actions', ['unit_id'], unique=False)
    op.create_index(op.f('ix_case_actions_performed_by_user_id'), 'case_actions', ['performed_by_user_id'], unique=False)
    op.create_index(op.f('ix_case_actions_action_at'), 'case_actions', ['action_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema for Step 7 Phase C."""
    op.drop_table('case_actions')
    op.drop_table('aicte_cases')
