"""remove branch info from branch

Revision ID: 0a7063c06398
Revises: eab55aea15c9
Create Date: 2024-12-01 10:42:26.271857

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a7063c06398'
down_revision = 'eab55aea15c9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Branches', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=sa.NVARCHAR(length=100, collation='Thai_CI_AS'),
               nullable=False)
        batch_op.drop_column('teamviewer_id')
        batch_op.drop_column('teamviewer_pwd')
        batch_op.drop_column('anydesk_id')
        batch_op.drop_column('anydesk_pwd')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Branches', schema=None) as batch_op:
        batch_op.add_column(sa.Column('anydesk_pwd', sa.VARCHAR(length=20, collation='SQL_Latin1_General_CP1_CI_AS'), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('anydesk_id', sa.VARCHAR(length=20, collation='SQL_Latin1_General_CP1_CI_AS'), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('teamviewer_pwd', sa.VARCHAR(length=20, collation='SQL_Latin1_General_CP1_CI_AS'), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('teamviewer_id', sa.VARCHAR(length=20, collation='SQL_Latin1_General_CP1_CI_AS'), autoincrement=False, nullable=True))
        batch_op.alter_column('name',
               existing_type=sa.NVARCHAR(length=100, collation='Thai_CI_AS'),
               nullable=True)

    # ### end Alembic commands ###