"""SQLite persistence for games and guesses (stdlib only)."""
import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(os.environ.get("WORDLE_DB", Path(__file__).parent / "data" / "wordle.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    id TEXT PRIMARY KEY,
    word_length INTEGER NOT NULL,
    answer TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'in_progress',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS guesses (
    game_id TEXT NOT NULL REFERENCES games(id),
    position INTEGER NOT NULL,
    word TEXT NOT NULL,
    feedback TEXT NOT NULL,
    PRIMARY KEY (game_id, position)
);
"""


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)


def create_game(word_length: int, answer: str) -> str:
    game_id = uuid.uuid4().hex
    with connect() as conn:
        conn.execute(
            "INSERT INTO games (id, word_length, answer) VALUES (?, ?, ?)",
            (game_id, word_length, answer),
        )
    return game_id


def get_game(game_id: str) -> dict | None:
    """Return the game row plus its ordered guesses, or None."""
    with connect() as conn:
        row = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if row is None:
            return None
        guesses = conn.execute(
            "SELECT word, feedback FROM guesses WHERE game_id = ? ORDER BY position",
            (game_id,),
        ).fetchall()
    game = dict(row)
    game["guesses"] = [{"word": g["word"], "feedback": g["feedback"].split(",")} for g in guesses]
    return game


def list_games() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """SELECT g.id, g.word_length, g.status, g.created_at,
                      (SELECT COUNT(*) FROM guesses WHERE game_id = g.id) AS guess_count
               FROM games g ORDER BY g.created_at DESC, g.rowid DESC"""
        ).fetchall()
    return [dict(r) for r in rows]


def add_guess(game_id: str, position: int, word: str, feedback: list[str], status: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO guesses (game_id, position, word, feedback) VALUES (?, ?, ?, ?)",
            (game_id, position, word, ",".join(feedback)),
        )
        conn.execute("UPDATE games SET status = ? WHERE id = ?", (status, game_id))
