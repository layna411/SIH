"""step7_phase_g_notification_lifecycle

Revision ID: g1b23c4d5e6f
Revises: f0a45b6c7d8e
Create Date: 2026-10-29 11:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g1b23c4d5e6f'
down_revision: Union[str, Sequence[str], None] = 'f0a45b6c7d8e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for Step 7 Phase G: Notification Lifecycle & Acknowledgement."""
    # Add lifecycle, acknowledgement, severity, category, and reference fields to notifications
    op.add_column(
        'notifications',
        sa.Column('requires_acknowledgement', sa.Boolean(), server_default='0', nullable=False)
    )
    op.add_column(
        'notifications',
        sa.Column('is_acknowledged', sa.Boolean(), server_default='0', nullable=False)
    )
    op.add_column(
        'notifications',
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True)
    )
    op.add_column(
        'notifications',
        sa.Column('severity', sa.String(length=20), server_default='INFO', nullable=False)
    )
    op.add_column(
        'notifications',
        sa.Column('category', sa.String(length=50), nullable=True)
    )
    op.add_column(
        'notifications',
        sa.Column('reference_id', sa.String(length=100), nullable=True)
    )

    op.create_index(op.f('ix_notifications_is_acknowledged'), 'notifications', ['is_acknowledged'], unique=False)
    op.create_index(op.f('ix_notifications_category'), 'notifications', ['category'], unique=False)
    op.create_index(op.f('ix_notifications_reference_id'), 'notifications', ['reference_id'], unique=False)
    op.create_index('ix_notifications_user_category_ref', 'notifications', ['user_id', 'category', 'reference_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema for Step 7 Phase G."""
    op.drop_index('ix_notifications_user_category_ref', table_name='notifications')
    op.drop_index(op.f('ix_notifications_reference_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_category'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_is_acknowledged'), table_name='notifications')

    op.drop_column('notifications', 'reference_id')
    op.drop_column('notifications', 'category')
    op.drop_column('notifications', 'severity')
    op.drop_column('notifications', 'acknowledged_at')
    op.drop_column('notifications', 'is_acknowledged')
    op.drop_column('notifications', 'requires_acknowledgement')
