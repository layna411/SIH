"""step2_models_roles_memberships

Revision ID: 3d89c6ffd0e5
Revises: 021be099e2a3
Create Date: 2026-10-28 09:30:28.753598

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d89c6ffd0e5'
down_revision: Union[str, Sequence[str], None] = '021be099e2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create roles table
    op.create_table('roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)

    # 2. Add columns to institution_memberships with safe server defaults
    op.add_column('institution_memberships', sa.Column('role_id', sa.Integer(), nullable=True))
    op.add_column('institution_memberships', sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_index(op.f('ix_institution_memberships_role_id'), 'institution_memberships', ['role_id'], unique=False)
    op.create_unique_constraint('uq_user_institution_membership', 'institution_memberships', ['user_id', 'institution_id'])
    op.create_foreign_key('fk_membership_role', 'institution_memberships', 'roles', ['role_id'], ['id'], ondelete='RESTRICT')

    # 3. Add columns to institutions with safe server defaults
    op.add_column('institutions', sa.Column('institution_type', sa.String(length=50), server_default='COLLEGE', nullable=True))
    op.add_column('institutions', sa.Column('district', sa.String(length=100), nullable=True))
    op.add_column('institutions', sa.Column('verification_status', sa.String(length=20), server_default='VERIFIED', nullable=False))
    op.add_column('institutions', sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))

    # 4. Add columns to regulatory_jurisdictions with safe server defaults
    op.add_column('regulatory_jurisdictions', sa.Column('jurisdiction_type', sa.String(length=50), server_default='STATE', nullable=False))
    op.add_column('regulatory_jurisdictions', sa.Column('region', sa.String(length=100), nullable=True))
    op.add_column('regulatory_jurisdictions', sa.Column('institution_id', sa.Integer(), nullable=True))
    op.add_column('regulatory_jurisdictions', sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False))
    op.add_column('regulatory_jurisdictions', sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_index(op.f('ix_regulatory_jurisdictions_institution_id'), 'regulatory_jurisdictions', ['institution_id'], unique=False)
    op.create_foreign_key('fk_jurisdiction_institution', 'regulatory_jurisdictions', 'institutions', ['institution_id'], ['id'], ondelete='SET NULL')

    # 5. Add columns to users
    op.add_column('users', sa.Column('is_email_verified', sa.Boolean(), server_default=sa.text('0'), nullable=False))

    # 6. Seed baseline roles
    roles_table = sa.table(
        'roles',
        sa.column('name', sa.String),
        sa.column('description', sa.String)
    )
    op.bulk_insert(roles_table, [
        {"name": "STUDENT", "description": "Enrolled student submitter with private grievance tracking"},
        {"name": "COLLEGE_OFFICER", "description": "Assigned college redressing officer with workflow authority"},
        {"name": "INSTITUTION_HEAD", "description": "Head of institution with executive college oversight"},
        {"name": "REGULATORY_ADMIN", "description": "Regional regulatory body administrator for compliance monitoring"},
        {"name": "SUPER_ADMIN", "description": "Master system administrator with full governance access"}
    ])

    # Link existing memberships if any
    op.execute(
        "UPDATE institution_memberships im "
        "JOIN roles r ON r.name = im.role "
        "SET im.role_id = r.id WHERE im.role_id IS NULL"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'is_email_verified')
    op.drop_constraint('fk_jurisdiction_institution', 'regulatory_jurisdictions', type_='foreignkey')
    op.drop_index(op.f('ix_regulatory_jurisdictions_institution_id'), table_name='regulatory_jurisdictions')
    op.drop_column('regulatory_jurisdictions', 'updated_at')
    op.drop_column('regulatory_jurisdictions', 'is_active')
    op.drop_column('regulatory_jurisdictions', 'institution_id')
    op.drop_column('regulatory_jurisdictions', 'region')
    op.drop_column('regulatory_jurisdictions', 'jurisdiction_type')
    op.drop_column('institutions', 'updated_at')
    op.drop_column('institutions', 'verification_status')
    op.drop_column('institutions', 'district')
    op.drop_column('institutions', 'institution_type')
    op.drop_constraint('fk_membership_role', 'institution_memberships', type_='foreignkey')
    op.drop_constraint('uq_user_institution_membership', 'institution_memberships', type_='unique')
    op.drop_index(op.f('ix_institution_memberships_role_id'), table_name='institution_memberships')
    op.drop_column('institution_memberships', 'updated_at')
    op.drop_column('institution_memberships', 'role_id')
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_index(op.f('ix_roles_id'), table_name='roles')
    op.drop_table('roles')
