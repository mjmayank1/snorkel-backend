"""make shorediving id unique

Revision ID: 4561393dfdd5
Revises: 884bcffa2fe1
Create Date: 2021-09-09 08:21:03.044878

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4561393dfdd5'
down_revision = '884bcffa2fe1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('uq_sd_review_id', 'shore_diving_review', ['shorediving_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('uq_sd_review_id', 'shore_diving_review', type_='unique')
    # ### end Alembic commands ###