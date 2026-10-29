"""step3_grievance_workflow_enhancements

Revision ID: 4f82a17c2b3e
Revises: 3d89c6ffd0e5
Create Date: 2026-10-28 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f82a17c2b3e'
down_revision: Union[str, Sequence[str], None] = '3d89c6ffd0e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for Step 3 grievance workflow enhancements."""
    # 1. Add unassigned_at timestamp to grievance_assignments
    op.add_column('grievance_assignments', sa.Column('unassigned_at', sa.DateTime(), nullable=True))

    # 2. Modify grievance_escalations to support nullable escalated_by_id (system process escalations)
    try:
        op.drop_constraint('grievance_escalations_ibfk_1', 'grievance_escalations', type_='foreignkey')
    except Exception:
        pass
    
    op.alter_column('grievance_escalations', 'escalated_by_id',
                    existing_type=sa.Integer(),
                    nullable=True)
    
    op.create_foreign_key('fk_escalation_user', 'grievance_escalations', 'users', ['escalated_by_id'], ['id'], ondelete='SET NULL')

    # 3. Add handling scope columns to grievance_escalations
    op.add_column('grievance_escalations', sa.Column('previous_handling_scope', sa.String(length=100), nullable=True))
    op.add_column('grievance_escalations', sa.Column('new_handling_scope', sa.String(length=100), nullable=True))

    # 4. Safe seed of default categories if missing
    bind = op.get_bind()
    categories_to_seed = [
        ('ACADEMIC', 'Academics & Teaching', 'Academic, syllabus, faculty and teaching concerns', 7),
        ('EXAM', 'Examinations & Results', 'Exam schedules, hall tickets, grading and evaluation', 5),
        ('FINANCE', 'Fees & Finance', 'Fee payments, receipts, dues and refunds', 7),
        ('SCHOLARSHIP', 'Scholarships & Financial Aid', 'Scholarship applications, verification and disbursements', 10),
        ('HOSTEL', 'Hostel & Accommodation', 'Hostel allotment, room maintenance, mess and amenities', 3),
        ('INFRA', 'Infrastructure & Facilities', 'Labs, classrooms, Wi-Fi, electricity and campus facilities', 5),
        ('ADMIN', 'Administration & Records', 'Certificates, identity cards, transcripts and official documents', 5),
        ('CONDUCT', 'Student Conduct & Anti-Ragging', 'Misconduct, discrimination, anti-ragging and harassment', 1),
        ('SUPPORT', 'Accessibility & Special Support', 'Disability support, medical emergencies and counseling', 2),
        ('OTHER', 'Other Concerns', 'General or uncategorized student grievances', 7)
    ]
    for code, name, desc, sla in categories_to_seed:
        res = bind.execute(sa.text("SELECT id FROM grievance_categories WHERE code = :code").bindparams(code=code)).first()
        if not res:
            bind.execute(
                sa.text(
                    "INSERT INTO grievance_categories (code, name, description, default_sla_days, is_active, created_at) "
                    "VALUES (:code, :name, :desc, :sla, 1, NOW())"
                ).bindparams(code=code, name=name, desc=desc, sla=sla)
            )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('grievance_escalations', 'new_handling_scope')
    op.drop_column('grievance_escalations', 'previous_handling_scope')
    try:
        op.drop_constraint('fk_escalation_user', 'grievance_escalations', type_='foreignkey')
    except Exception:
        pass
    op.alter_column('grievance_escalations', 'escalated_by_id',
                    existing_type=sa.Integer(),
                    nullable=False)
    op.create_foreign_key('grievance_escalations_ibfk_1', 'grievance_escalations', 'users', ['escalated_by_id'], ['id'], ondelete='RESTRICT')
    op.drop_column('grievance_assignments', 'unassigned_at')
