"""
Initial PostgreSQL schema migration.
Creates tables for animal types and breeds (master data).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create initial schema for master data."""
    
    # Create animal_types table
    op.create_table(
        'animal_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_animal_types_name'), 'animal_types', ['name'], unique=False)
    
    # Create breeds table
    op.create_table(
        'breeds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('animal_type_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('origin', sa.String(length=100), nullable=True),
        sa.Column('characteristics', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
        sa.ForeignKeyConstraint(['animal_type_id'], ['animal_types.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'animal_type_id')
    )
    op.create_index(op.f('ix_breeds_name'), 'breeds', ['name'], unique=False)


def downgrade():
    """Remove initial schema."""
    op.drop_index(op.f('ix_breeds_name'), table_name='breeds')
    op.drop_table('breeds')
    op.drop_index(op.f('ix_animal_types_name'), table_name='animal_types')
    op.drop_table('animal_types')
