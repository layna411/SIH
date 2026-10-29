"""step7_phase_d_aicte_case_overlaps_and_links

Revision ID: e9f34a5b6c7d
Revises: d8c23e4f5a6b
Create Date: 2026-10-29 10:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9f34a5b6c7d'
down_revision: Union[str, Sequence[str], None] = 'd8c23e4f5a6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for Step 7 Phase D: AICTE Case Overlaps & Case Links."""
    # 1. Create aicte_case_overlaps table
    op.create_table(
        'aicte_case_overlaps',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('case_id_low', sa.Integer(), nullable=False),
        sa.Column('case_id_high', sa.Integer(), nullable=False),
        sa.Column('overlap_type', sa.String(length=50), nullable=False),
        sa.Column('match_score', sa.Float(), nullable=True),
        sa.Column('match_reasons', sa.Text(), nullable=False),
        sa.Column('detection_method', sa.String(length=50), server_default='RULE_BASED', nullable=False),
        sa.Column('review_status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('detected_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['case_id_high'], ['aicte_cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['case_id_low'], ['aicte_cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('case_id_low', 'case_id_high', name='uq_aicte_case_overlap_pair'),
        sa.CheckConstraint('case_id_low < case_id_high', name='chk_aicte_case_overlap_canonical_pair')
    )
    op.create_index(op.f('ix_aicte_case_overlaps_id'), 'aicte_case_overlaps', ['id'], unique=False)
    op.create_index(op.f('ix_aicte_case_overlaps_case_id_low'), 'aicte_case_overlaps', ['case_id_low'], unique=False)
    op.create_index(op.f('ix_aicte_case_overlaps_case_id_high'), 'aicte_case_overlaps', ['case_id_high'], unique=False)
    op.create_index(op.f('ix_aicte_case_overlaps_overlap_type'), 'aicte_case_overlaps', ['overlap_type'], unique=False)
    op.create_index(op.f('ix_aicte_case_overlaps_review_status'), 'aicte_case_overlaps', ['review_status'], unique=False)
    op.create_index(op.f('ix_aicte_case_overlaps_detected_at'), 'aicte_case_overlaps', ['detected_at'], unique=False)

    # 2. Create aicte_case_links table
    op.create_table(
        'aicte_case_links',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('case_id_low', sa.Integer(), nullable=False),
        sa.Column('case_id_high', sa.Integer(), nullable=False),
        sa.Column('link_type', sa.String(length=50), nullable=False),
        sa.Column('source_overlap_id', sa.Integer(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['case_id_high'], ['aicte_cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['case_id_low'], ['aicte_cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['source_overlap_id'], ['aicte_case_overlaps.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('case_id_low', 'case_id_high', 'link_type', name='uq_aicte_case_link_type'),
        sa.CheckConstraint('case_id_low < case_id_high', name='chk_aicte_case_link_canonical_pair')
    )
    op.create_index(op.f('ix_aicte_case_links_id'), 'aicte_case_links', ['id'], unique=False)
    op.create_index(op.f('ix_aicte_case_links_case_id_low'), 'aicte_case_links', ['case_id_low'], unique=False)
    op.create_index(op.f('ix_aicte_case_links_case_id_high'), 'aicte_case_links', ['case_id_high'], unique=False)
    op.create_index(op.f('ix_aicte_case_links_link_type'), 'aicte_case_links', ['link_type'], unique=False)
    op.create_index(op.f('ix_aicte_case_links_is_active'), 'aicte_case_links', ['is_active'], unique=False)


def downgrade() -> None:
    """Downgrade schema for Step 7 Phase D."""
    op.drop_index(op.f('ix_aicte_case_links_is_active'), table_name='aicte_case_links')
    op.drop_index(op.f('ix_aicte_case_links_link_type'), table_name='aicte_case_links')
    op.drop_index(op.f('ix_aicte_case_links_case_id_high'), table_name='aicte_case_links')
    op.drop_index(op.f('ix_aicte_case_links_case_id_low'), table_name='aicte_case_links')
    op.drop_index(op.f('ix_aicte_case_links_id'), table_name='aicte_case_links')
    op.drop_table('aicte_case_links')

    op.drop_index(op.f('ix_aicte_case_overlaps_detected_at'), table_name='aicte_case_overlaps')
    op.drop_index(op.f('ix_aicte_case_overlaps_review_status'), table_name='aicte_case_overlaps')
    op.drop_index(op.f('ix_aicte_case_overlaps_overlap_type'), table_name='aicte_case_overlaps')
    op.drop_index(op.f('ix_aicte_case_overlaps_case_id_high'), table_name='aicte_case_overlaps')
    op.drop_index(op.f('ix_aicte_case_overlaps_case_id_low'), table_name='aicte_case_overlaps')
    op.drop_index(op.f('ix_aicte_case_overlaps_id'), table_name='aicte_case_overlaps')
    op.drop_table('aicte_case_overlaps')
