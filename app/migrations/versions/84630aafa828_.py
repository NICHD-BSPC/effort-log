"""empty message

Revision ID: 84630aafa828
Revises: 
Create Date: 2021-02-06 21:19:05.252604

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '84630aafa828'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('entry',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('pi', sa.String(length=64), nullable=True),
    sa.Column('project', sa.String(length=120), nullable=True),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('personnel', sa.String(length=64), nullable=True),
    sa.Column('fraction', sa.Float(), nullable=True),
    sa.Column('notes', sa.String(length=1000), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_entry_date'), 'entry', ['date'], unique=False)
    op.create_index(op.f('ix_entry_personnel'), 'entry', ['personnel'], unique=False)
    op.create_index(op.f('ix_entry_pi'), 'entry', ['pi'], unique=False)
    op.create_index(op.f('ix_entry_project'), 'entry', ['project'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_entry_project'), table_name='entry')
    op.drop_index(op.f('ix_entry_pi'), table_name='entry')
    op.drop_index(op.f('ix_entry_personnel'), table_name='entry')
    op.drop_index(op.f('ix_entry_date'), table_name='entry')
    op.drop_table('entry')
    # ### end Alembic commands ###
