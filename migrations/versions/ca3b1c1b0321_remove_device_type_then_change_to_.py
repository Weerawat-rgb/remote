"""remove device_type then change to machine_type in devices

Revision ID: ca3b1c1b0321
Revises: 8c786a1835b0
Create Date: 2024-12-01 12:04:10.103657

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ca3b1c1b0321'
down_revision = '8c786a1835b0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Devices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('branch_id', sa.Integer(), nullable=False),
    sa.Column('machine_type', sa.String(length=50), nullable=True),
    sa.Column('teamviewer_id', sa.String(length=50), nullable=True),
    sa.Column('teamviewer_pwd', sa.String(length=50), nullable=True),
    sa.Column('anydesk_id', sa.String(length=50), nullable=True),
    sa.Column('anydesk_pwd', sa.String(length=50), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('isactive', sa.Boolean(), nullable=True),
    sa.Column('last_updated', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['branch_id'], ['Branches.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Devices')
    # ### end Alembic commands ###