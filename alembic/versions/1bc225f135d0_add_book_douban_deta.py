"""add book douban details row

Revision ID: 1bc225f135d0
Revises: None
Create Date: 2013-10-13 10:33:25.509756

"""

# revision identifiers, used by Alembic.
revision = '1bc225f135d0'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('book', sa.Column('douban_details', sa.String(5000)))


def downgrade():
    op.drop_column('book', 'douban_details')
