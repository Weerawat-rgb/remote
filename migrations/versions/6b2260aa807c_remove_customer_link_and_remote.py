"""Remove customer link and remote

Revision ID: 6b2260aa807c
Revises: d1c90de0d1bf
Create Date: 2024-12-03 14:05:53.519731

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b2260aa807c'
down_revision = 'd1c90de0d1bf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Customers', schema=None) as batch_op:
        batch_op.drop_column('anydesk_pwd')
        batch_op.drop_column('hostname')
        batch_op.drop_column('password')
        batch_op.drop_column('teamviewer_pwd')
        batch_op.drop_column('username')
        batch_op.drop_column('teamviewer_id')
        batch_op.drop_column('anydesk_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Customers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('anydesk_id', sa.VARCHAR(length=50, collation='Thai_CI_AS'), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('teamviewer_id', sa.VARCHAR(length=50, collation='Thai_CI_AS'), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('username', sa.VARCHAR(length=50, collation='Thai_CI_AS'), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('teamviewer_pwd', sa.VARCHAR(length=50, collation='Thai_CI_AS'), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('password', sa.VARCHAR(length=50, collation='Thai_CI_AS'), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('hostname', sa.VARCHAR(length=100, collation='Thai_CI_AS'), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('anydesk_pwd', sa.VARCHAR(length=50, collation='Thai_CI_AS'), autoincrement=False, nullable=True))

    # ### end Alembic commands ###
