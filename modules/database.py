# -*- coding: utf-8 -*-
"""
database.py - SQLite persistence layer for the Green Ledger.

On Streamlit Cloud, the DB file lives in /tmp (ephemeral per-instance,
persists across page refreshes for the lifetime of the running container).
Locally it lives in the project root as heat_sync.db.

To upgrade to Supabase later: swap get_connection() with a psycopg2/asyncpg
connection - the rest of the API stays identical.
"""

import sqlite3
import os
from typing import Optional, List, Dict
from datetime import datetime

# ---------------------------------------------------------------------------
# DB path: /tmp on Cloud (writable), project root locally
# ---------------------------------------------------------------------------
_IS_CLOUD = os.environ.get("HOME", "") == "/home/appuser"
_DB_PATH = "/tmp/heat_sync.db" if _IS_CLOUD else os.path.join(
    os.path.dirname(__file__), "..", "heat_sync.db"
)


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite DB, thread-safe (check_same_thread=False for Streamlit)."""
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Enables dict-style row access
    return conn


def init_db():
    """Create tables if they don't exist. Safe to call on every app boot."""
    conn = get_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS green_ledger (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       TEXT    NOT NULL,
                nature_id_hash  TEXT    NOT NULL UNIQUE,
                city            TEXT    NOT NULL DEFAULT 'Unknown',
                target_asset    TEXT    NOT NULL,
                intervention    TEXT    NOT NULL,
                cooling_impact  TEXT    NOT NULL,
                cost            REAL    NOT NULL DEFAULT 0.0,
                status          TEXT    NOT NULL DEFAULT 'Verified ✅'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nature_assets (
                asset_id    TEXT PRIMARY KEY,
                osm_id      TEXT,
                city        TEXT    NOT NULL DEFAULT 'Unknown',
                asset_type  TEXT    NOT NULL,
                lat         REAL    NOT NULL,
                lon         REAL    NOT NULL,
                created_at  TEXT    NOT NULL
            )
        """)
    conn.close()


# ---------------------------------------------------------------------------
# Green Ledger
# ---------------------------------------------------------------------------

def save_ledger_entry(
    nature_id_hash: str,
    city: str,
    target_asset: str,
    intervention: str,
    cooling_impact: str,
    cost: float,
    status: str = "Verified ✅",
) -> bool:
    """
    Insert a single Green Ledger row.
    Returns True on success, False if the hash already exists (idempotent).
    """
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO green_ledger
                    (timestamp, nature_id_hash, city, target_asset, intervention,
                     cooling_impact, cost, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                    nature_id_hash,
                    city,
                    target_asset,
                    intervention,
                    cooling_impact,
                    cost,
                    status,
                ),
            )
        return True
    except sqlite3.IntegrityError:
        # Duplicate hash — already saved, skip silently
        return False
    finally:
        conn.close()


def load_ledger_entries(city: Optional[str] = None) -> List[Dict]:
    """
    Load all Green Ledger rows, optionally filtered by city.
    Returns a list of dicts matching the display column names used in the UI.
    """
    conn = get_connection()
    try:
        if city:
            rows = conn.execute(
                "SELECT * FROM green_ledger WHERE city = ? ORDER BY id DESC",
                (city,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM green_ledger ORDER BY id DESC"
            ).fetchall()

        # Map to the column names the UI dataframe expects
        return [
            {
                "Timestamp":          row["timestamp"],
                "Nature ID":          row["nature_id_hash"],
                "City":               row["city"],
                "Target Asset":       row["target_asset"],
                "Intervention":       row["intervention"],
                "Cooling Impact (°C)":row["cooling_impact"],
                "Cost ($)":           f"${row['cost']:,.0f}",
                "Status":             row["status"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def clear_ledger_entries(city: Optional[str] = None):
    """Delete all ledger rows, optionally scoped to a city (for sandbox reset)."""
    conn = get_connection()
    with conn:
        if city:
            conn.execute("DELETE FROM green_ledger WHERE city = ?", (city,))
        else:
            conn.execute("DELETE FROM green_ledger")
    conn.close()


# ---------------------------------------------------------------------------
# Nature Assets (future use)
# ---------------------------------------------------------------------------

def upsert_nature_asset(
    asset_id: str,
    osm_id: str,
    city: str,
    asset_type: str,
    lat: float,
    lon: float,
):
    """Insert or replace a Nature ID asset record."""
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO nature_assets
                (asset_id, osm_id, city, asset_type, lat, lon, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (asset_id, osm_id, city, asset_type, lat, lon,
             datetime.now().isoformat()),
        )
    conn.close()
