"""empty message

Revision ID: fd041aec0ca4
Revises: 6413d3154341
Create Date: 2020-02-15 18:31:52.621798

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd041aec0ca4'
down_revision = '6413d3154341'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Artist', 'genres')
    op.drop_column('Venue', 'genres')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Venue', sa.Column('genres', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('Artist', sa.Column('genres', sa.VARCHAR(length=120), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
