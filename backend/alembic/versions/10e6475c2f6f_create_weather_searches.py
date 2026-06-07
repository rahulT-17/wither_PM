"""create weather_searches

Revision ID: 10e6475c2f6f
Revises:
Create Date: 2026-05-30 15:57:10.188030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "10e6475c2f6f"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    units_enum = postgresql.ENUM(
        "metric",
        "imperial",
        "standard",
        name="units",
        create_type=False,
    )
    units_enum.create(bind, checkfirst=True)

    op.create_table(
        "weather_searches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("resolved_city", sa.String(length=255), nullable=True),
        sa.Column("country_code", sa.String(length=8), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("units", units_enum, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("weather_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_weather_searches_created_at", "weather_searches", ["created_at"], unique=False)
    op.create_index(op.f("ix_weather_searches_id"), "weather_searches", ["id"], unique=False)
    op.create_index("ix_weather_searches_location", "weather_searches", ["location"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index("ix_weather_searches_location", table_name="weather_searches")
    op.drop_index(op.f("ix_weather_searches_id"), table_name="weather_searches")
    op.drop_index("ix_weather_searches_created_at", table_name="weather_searches")
    op.drop_table("weather_searches")
    postgresql.ENUM(
        "metric",
        "imperial",
        "standard",
        name="units",
        create_type=False,
    ).drop(bind, checkfirst=True)
