"""add bot settings and resto api fields

Revision ID: f0f0cb77266c
Revises: 9f313d1f2e83
Create Date: 2026-04-01 17:51:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision = 'f0f0cb77266c'
down_revision = '9f313d1f2e83'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create bot_settings table
    op.create_table('bot_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_bot_token', sa.String(length=500), nullable=True),
        sa.Column('welcome_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add columns to iiko_settings
    op.add_column('iiko_settings', sa.Column('resto_url', sa.String(length=500), nullable=True))
    op.add_column('iiko_settings', sa.Column('resto_login', sa.String(length=255), nullable=True))
    op.add_column('iiko_settings', sa.Column('resto_password', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('iiko_settings', 'resto_password')
    op.drop_column('iiko_settings', 'resto_login')
    op.drop_column('iiko_settings', 'resto_url')
    op.drop_table('bot_settings')
