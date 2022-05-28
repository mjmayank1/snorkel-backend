"""add owner user id to dive shop Model

Revision ID: 68b56a7e8edb
Revises: af11b5deeae9
Create Date: 2022-05-24 07:04:17.274334

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '68b56a7e8edb'
down_revision = 'af11b5deeae9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('dive_shop', sa.Column('owner_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'dive_shop', 'user', ['owner_user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'dive_shop', type_='foreignkey')
    op.drop_column('dive_shop', 'owner_user_id')
    # ### end Alembic commands ###