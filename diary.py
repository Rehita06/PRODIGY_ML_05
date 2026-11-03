"""Food diary stored in a small local SQLite file (nutrilens.db).

SQLite ships with Python, so nothing extra to install. The database stays on your
own computer. Delete nutrilens.db to start fresh.
"""

import json
import sqlite3
from contextlib import closing
from datetime import date, datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).with_name("nutrilens.db")


def _connect(path=None):
    return sqlite3.connect(str(path or DB_PATH))


def init_db(path=None):
    with closing(_connect(path)) as conn, conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT NOT NULL,
                logged_at TEXT NOT NULL,
                meal TEXT NOT NULL,
                food TEXT NOT NULL,
                grams REAL,
                calories REAL NOT NULL,
                protein_g REAL NOT NULL,
                carbs_g REAL NOT NULL,
                fat_g REAL NOT NULL,
                source TEXT NOT NULL
            )"""
        )
        conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")


def add_entry(food, meal, calories, protein_g, carbs_g, fat_g, source, grams=None, day=None, path=None):
    """Save one food entry and return its id."""
    now = datetime.now()
    day = day or date.today().isoformat()
    with closing(_connect(path)) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO entries (day, logged_at, meal, food, grams, calories, protein_g, carbs_g, fat_g, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (day, now.isoformat(timespec="seconds"), meal, str(food)[:120], grams,
             float(calories), float(protein_g), float(carbs_g), float(fat_g), source),
        )
        return cursor.lastrowid


def entries_for_day(day=None, path=None):
    day = day or date.today().isoformat()
    with closing(_connect(path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM entries WHERE day = ? ORDER BY id", (day,)).fetchall()
    return [dict(row) for row in rows]


def all_entries(path=None):
    with closing(_connect(path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM entries ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def delete_entry(entry_id, path=None):
    with closing(_connect(path)) as conn, conn:
        conn.execute("DELETE FROM entries WHERE id = ?", (int(entry_id),))


def totals(entries):
    return {
        "calories": round(sum(e["calories"] for e in entries)),
        "protein_g": round(sum(e["protein_g"] for e in entries), 1),
        "carbs_g": round(sum(e["carbs_g"] for e in entries), 1),
        "fat_g": round(sum(e["fat_g"] for e in entries), 1),
    }


def daily_totals(days=7, path=None):
    """Totals for each of the last `days` days (oldest first), including empty days."""
    start = date.today() - timedelta(days=days - 1)
    with closing(_connect(path)) as conn:
        rows = conn.execute(
            "SELECT day, SUM(calories), SUM(protein_g), SUM(carbs_g), SUM(fat_g) "
            "FROM entries WHERE day >= ? GROUP BY day",
            (start.isoformat(),),
        ).fetchall()
    found = {r[0]: r for r in rows}
    result = []
    for offset in range(days):
        day = (start + timedelta(days=offset)).isoformat()
        row = found.get(day)
        result.append({
            "day": day,
            "calories": round(row[1]) if row else 0,
            "protein_g": round(row[2], 1) if row else 0,
            "carbs_g": round(row[3], 1) if row else 0,
            "fat_g": round(row[4], 1) if row else 0,
        })
    return result


def save_profile(profile, path=None):
    with closing(_connect(path)) as conn, conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('profile', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (json.dumps(profile),),
        )


def load_profile(path=None):
    with closing(_connect(path)) as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = 'profile'").fetchone()
    if not row:
        return None
    try:
        return json.loads(row[0])
    except ValueError:
        return None
