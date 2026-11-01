"""
Lightweight SQLite-backed player progression store.

Used by the server to persist cumulative XP/stats across rounds so
returning players (matched by name) keep their progression. Entirely
optional to the core loop — if the DB can't be opened for any reason,
callers should treat failures as non-fatal.
"""
import sqlite3
import threading

from config import settings

_lock = threading.Lock()


def _connect():
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS player_stats_v2 (
            profile_id TEXT PRIMARY KEY,
            name TEXT,
            total_xp INTEGER DEFAULT 0,
            rounds_played INTEGER DEFAULT 0,
            rounds_won INTEGER DEFAULT 0,
            eliminations INTEGER DEFAULT 0,
            objectives_completed INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    return conn


class StatsDB:
    def __init__(self):
        self._conn = None
        try:
            self._conn = _connect()
        except sqlite3.Error as e:
            print(f"[stats] disabled, could not open DB: {e}")

    def record_round(self, profile_id, name, xp_gained, won, eliminations, objectives_completed):
        if not self._conn:
            return
        with _lock:
            try:
                cur = self._conn.execute("SELECT total_xp FROM player_stats_v2 WHERE profile_id = ?", (profile_id,))
                row = cur.fetchone()
                if row is None:
                    self._conn.execute(
                        "INSERT INTO player_stats_v2 (profile_id, name, total_xp, rounds_played, rounds_won, "
                        "eliminations, objectives_completed) VALUES (?, ?, ?, 1, ?, ?, ?)",
                        (profile_id, name, xp_gained, 1 if won else 0, eliminations, objectives_completed),
                    )
                else:
                    self._conn.execute(
                        "UPDATE player_stats_v2 SET name = ?, total_xp = ?, rounds_played = rounds_played + 1, "
                        "rounds_won = rounds_won + ?, eliminations = eliminations + ?, "
                        "objectives_completed = objectives_completed + ? WHERE profile_id = ?",
                        (name, xp_gained, 1 if won else 0, eliminations, objectives_completed, profile_id),
                    )
                self._conn.commit()
            except sqlite3.Error as e:
                print(f"[stats] write failed: {e}")

    def get_stats(self, profile_id):
        if not self._conn:
            return None
        cur = self._conn.execute(
            "SELECT total_xp, rounds_played, rounds_won, eliminations, objectives_completed "
            "FROM player_stats_v2 WHERE profile_id = ?", (profile_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "total_xp": row[0], "rounds_played": row[1], "rounds_won": row[2],
            "eliminations": row[3], "objectives_completed": row[4],
        }
