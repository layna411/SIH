"""step7_phase_b_institutions_and_bureau_units

Revision ID: c7b12d3e4f5a
Revises: 59f5f8fb2f6b
Create Date: 2026-10-29 09:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7b12d3e4f5a'
down_revision: Union[str, Sequence[str], None] = '59f5f8fb2f6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for Step 7 Phase B: Institution Identity & AICTE Organizational Units."""
    # 1. Extend institutions table
    op.add_column('institutions', sa.Column('aicte_permanent_id', sa.String(length=50), nullable=True))
    op.add_column('institutions', sa.Column('region', sa.String(length=50), nullable=True))
    op.add_column('institutions', sa.Column('is_aicte_verified', sa.Boolean(), server_default=sa.text('0'), nullable=False))
    op.create_index(op.f('ix_institutions_aicte_permanent_id'), 'institutions', ['aicte_permanent_id'], unique=True)
    op.create_index(op.f('ix_institutions_region'), 'institutions', ['region'], unique=False)

    # 2. Create institution_aliases table
    op.create_table(
        'institution_aliases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('alias_name', sa.String(length=255), nullable=False),
        sa.Column('normalized_alias', sa.String(length=255), nullable=False),
        sa.Column('source', sa.String(length=100), server_default='MANUAL', nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('institution_id', 'normalized_alias', name='uq_institution_normalized_alias')
    )
    op.create_index(op.f('ix_institution_aliases_alias_name'), 'institution_aliases', ['alias_name'], unique=False)
    op.create_index(op.f('ix_institution_aliases_id'), 'institution_aliases', ['id'], unique=False)
    op.create_index(op.f('ix_institution_aliases_institution_id'), 'institution_aliases', ['institution_id'], unique=False)
    op.create_index(op.f('ix_institution_aliases_normalized_alias'), 'institution_aliases', ['normalized_alias'], unique=False)

    # 3. Create organizational_units table
    op.create_table(
        'organizational_units',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('unit_type', sa.String(length=50), server_default='BUREAU', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_unit_id', sa.Integer(), nullable=True),
        sa.Column('region_code', sa.String(length=50), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['parent_unit_id'], ['organizational_units.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizational_units_code'), 'organizational_units', ['code'], unique=True)
    op.create_index(op.f('ix_organizational_units_id'), 'organizational_units', ['id'], unique=False)
    op.create_index(op.f('ix_organizational_units_parent_unit_id'), 'organizational_units', ['parent_unit_id'], unique=False)

    # 4. Create bureau_memberships table
    op.create_table(
        'bureau_memberships',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('organizational_unit_id', sa.Integer(), nullable=False),
        sa.Column('membership_role', sa.String(length=50), server_default='BUREAU_OFFICER', nullable=False),
        sa.Column('designation', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('assigned_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organizational_unit_id'], ['organizational_units.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'organizational_unit_id', name='uq_user_bureau_membership')
    )
    op.create_index(op.f('ix_bureau_memberships_id'), 'bureau_memberships', ['id'], unique=False)
    op.create_index(op.f('ix_bureau_memberships_organizational_unit_id'), 'bureau_memberships', ['organizational_unit_id'], unique=False)
    op.create_index(op.f('ix_bureau_memberships_user_id'), 'bureau_memberships', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema for Step 7 Phase B."""
    op.drop_index(op.f('ix_bureau_memberships_user_id'), table_name='bureau_memberships')
    op.drop_index(op.f('ix_bureau_memberships_organizational_unit_id'), table_name='bureau_memberships')
    op.drop_index(op.f('ix_bureau_memberships_id'), table_name='bureau_memberships')
    op.drop_table('bureau_memberships')

    op.drop_index(op.f('ix_organizational_units_parent_unit_id'), table_name='organizational_units')
    op.drop_index(op.f('ix_organizational_units_id'), table_name='organizational_units')
    op.drop_index(op.f('ix_organizational_units_code'), table_name='organizational_units')
    op.drop_table('organizational_units')

    op.drop_index(op.f('ix_institution_aliases_normalized_alias'), table_name='institution_aliases')
    op.drop_index(op.f('ix_institution_aliases_institution_id'), table_name='institution_aliases')
    op.drop_index(op.f('ix_institution_aliases_id'), table_name='institution_aliases')
    op.drop_index(op.f('ix_institution_aliases_alias_name'), table_name='institution_aliases')
    op.drop_table('institution_aliases')

    op.drop_index(op.f('ix_institutions_region'), table_name='institutions')
    op.drop_index(op.f('ix_institutions_aicte_permanent_id'), table_name='institutions')
    op.drop_column('institutions', 'is_aicte_verified')
    op.drop_column('institutions', 'region')
    op.drop_column('institutions', 'aicte_permanent_id')
