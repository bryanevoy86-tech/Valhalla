import os
from typing import Optional

import psycopg2


def get_conn(dsn: Optional[str] = None):
    """
    Returns a psycopg2 connection with autocommit=True.
    DSN is taken from env DATABASE_URL or falls back to localhost.
    """
    dsn = dsn or os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/valhalla",
    )
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    return conn
