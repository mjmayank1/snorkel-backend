"""add name to dive shop

Revision ID: 44d4df0fe283
Revises: 2f4db5864a2d
Create Date: 2022-06-04 21:56:34.510762

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '44d4df0fe283'
down_revision = '2f4db5864a2d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('dive_shop', sa.Column('name', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('dive_shop', 'name')
    # ### end Alembic commands ###