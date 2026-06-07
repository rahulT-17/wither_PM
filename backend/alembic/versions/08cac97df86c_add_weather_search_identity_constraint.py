"""add search_key to weather_searches

Revision ID: 08cac97df86c
Revises: 10e6475c2f6f
Create Date: 2026-06-02 21:40:38.339460

"""
from hashlib import sha256
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "08cac97df86c"
down_revision: Union[str, None] = "10e6475c2f6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def build_key(location, resolved_city, country_code, units, start_date, end_date) -> str:
    parts = [
        " ".join((location or "").strip().lower().split()),
        " ".join((resolved_city or "").strip().lower().split()),
        (country_code or "").strip().upper(),
        str(units or ""),
        start_date.isoformat() if start_date else "",
        end_date.isoformat() if end_date else "",
    ]
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def upgrade() -> None:
    op.add_column("weather_searches", sa.Column("search_key", sa.String(length=64), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT id, location, resolved_city, country_code, units, start_date, end_date
            FROM weather_searches
            ORDER BY id
            """
        )
    ).mappings().all()

    for row in rows:
        conn.execute(
            sa.text("UPDATE weather_searches SET search_key = :search_key WHERE id = :id"),
            {
                "search_key": build_key(
                    row["location"],
                    row["resolved_city"],
                    row["country_code"],
                    row["units"],
                    row["start_date"],
                    row["end_date"],
                ),
                "id": row["id"],
            },
        )

    op.execute(sa.text("ALTER TABLE weather_searches DROP CONSTRAINT IF EXISTS uq_weather_search_identity"))
    op.alter_column("weather_searches", "search_key", nullable=False)
    op.create_unique_constraint(
        "uq_weather_searches_search_key",
        "weather_searches",
        ["search_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_weather_searches_search_key", "weather_searches", type_="unique")
    op.execute(sa.text("ALTER TABLE weather_searches DROP CONSTRAINT IF EXISTS uq_weather_search_identity"))
    op.drop_column("weather_searches", "search_key")
