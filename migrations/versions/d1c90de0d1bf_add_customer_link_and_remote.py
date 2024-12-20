"""Add customer link and remote

Revision ID: d1c90de0d1bf
Revises: e8818afe8cc3
Create Date: 2024-12-03 14:00:54.851543

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1c90de0d1bf'
down_revision = 'e8818afe8cc3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Customers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('teamviewer_id', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('teamviewer_pwd', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('anydesk_id', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('anydesk_pwd', sa.String(length=50), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Customers', schema=None) as batch_op:
        batch_op.drop_column('anydesk_pwd')
        batch_op.drop_column('anydesk_id')
        batch_op.drop_column('teamviewer_pwd')
        batch_op.drop_column('teamviewer_id')

    # ### end Alembic commands ###
