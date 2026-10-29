"""step7_phase_e_aicte_case_transfers

Revision ID: f0a45b6c7d8e
Revises: e9f34a5b6c7d
Create Date: 2026-10-29 10:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0a45b6c7d8e'
down_revision: Union[str, Sequence[str], None] = 'e9f34a5b6c7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for Step 7 Phase E: AICTE Inter-Bureau Case Transfers."""
    op.create_table(
        'aicte_case_transfers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('from_unit_id', sa.Integer(), nullable=False),
        sa.Column('to_unit_id', sa.Integer(), nullable=False),
        sa.Column('initiated_by_user_id', sa.Integer(), nullable=False),
        sa.Column('proposed_assignee_id', sa.Integer(), nullable=True),
        sa.Column('transfer_reason', sa.Text(), nullable=False),
        sa.Column('handover_summary', sa.Text(), nullable=True),
        sa.Column('prior_case_status', sa.String(length=50), nullable=False),
        sa.Column('transfer_status', sa.String(length=50), server_default='PENDING_ACCEPTANCE', nullable=False),
        sa.Column('initiated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('responded_by_user_id', sa.Integer(), nullable=True),
        sa.Column('response_notes', sa.Text(), nullable=True),
        sa.Column('accepted_assignee_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['aicte_cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_unit_id'], ['organizational_units.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['to_unit_id'], ['organizational_units.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['initiated_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['proposed_assignee_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['responded_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['accepted_assignee_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('from_unit_id != to_unit_id', name='chk_aicte_transfer_diff_units')
    )
    op.create_index(op.f('ix_aicte_case_transfers_id'), 'aicte_case_transfers', ['id'], unique=False)
    op.create_index(op.f('ix_aicte_case_transfers_case_id'), 'aicte_case_transfers', ['case_id'], unique=False)
    op.create_index(op.f('ix_aicte_case_transfers_from_unit_id'), 'aicte_case_transfers', ['from_unit_id'], unique=False)
    op.create_index(op.f('ix_aicte_case_transfers_to_unit_id'), 'aicte_case_transfers', ['to_unit_id'], unique=False)
    op.create_index(op.f('ix_aicte_case_transfers_transfer_status'), 'aicte_case_transfers', ['transfer_status'], unique=False)
    op.create_index(op.f('ix_aicte_case_transfers_initiated_at'), 'aicte_case_transfers', ['initiated_at'], unique=False)
    op.create_index('ix_aicte_transfers_case_status', 'aicte_case_transfers', ['case_id', 'transfer_status'], unique=False)
    op.create_index('ix_aicte_transfers_to_unit_status', 'aicte_case_transfers', ['to_unit_id', 'transfer_status'], unique=False)
    op.create_index('ix_aicte_transfers_from_unit_status', 'aicte_case_transfers', ['from_unit_id', 'transfer_status'], unique=False)


def downgrade() -> None:
    """Downgrade schema for Step 7 Phase E."""
    op.drop_index('ix_aicte_transfers_from_unit_status', table_name='aicte_case_transfers')
    op.drop_index('ix_aicte_transfers_to_unit_status', table_name='aicte_case_transfers')
    op.drop_index('ix_aicte_transfers_case_status', table_name='aicte_case_transfers')
    op.drop_index(op.f('ix_aicte_case_transfers_initiated_at'), table_name='aicte_case_transfers')
    op.drop_index(op.f('ix_aicte_case_transfers_transfer_status'), table_name='aicte_case_transfers')
    op.drop_index(op.f('ix_aicte_case_transfers_to_unit_id'), table_name='aicte_case_transfers')
    op.drop_index(op.f('ix_aicte_case_transfers_from_unit_id'), table_name='aicte_case_transfers')
    op.drop_index(op.f('ix_aicte_case_transfers_case_id'), table_name='aicte_case_transfers')
    op.drop_index(op.f('ix_aicte_case_transfers_id'), table_name='aicte_case_transfers')
    op.drop_table('aicte_case_transfers')
