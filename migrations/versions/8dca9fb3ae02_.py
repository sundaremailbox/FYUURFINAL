"""empty message

Revision ID: 8dca9fb3ae02
Revises: 7e9e2a511f91
Create Date: 2020-02-15 18:50:28.570882

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8dca9fb3ae02'
down_revision = '7e9e2a511f91'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('seeking_description', sa.String(length=255), nullable=True))
    op.drop_column('Artist', 'seeking_venue_desc')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('seeking_venue_desc', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.drop_column('Artist', 'seeking_description')
    # ### end Alembic commands ###
