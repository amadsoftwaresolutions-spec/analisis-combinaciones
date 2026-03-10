"""
Gestión de la base de datos SQLite para el análisis de combinaciones de lotería.
"""
import sqlite3
import json
import os
from datetime import datetime
from config import DB_PATH


class Database:
    """Maneja todas las operaciones de persistencia."""

    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._init_db()

    # ──────────────────────── conexión ────────────────────────
    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS lotteries (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT    NOT NULL UNIQUE,
                    positions   INTEGER NOT NULL,
                    min_number  INTEGER NOT NULL DEFAULT 1,
                    max_number  INTEGER NOT NULL,
                    created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS draws (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    lottery_id  INTEGER NOT NULL,
                    draw_date   TEXT,
                    numbers     TEXT    NOT NULL,
                    created_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lottery_id) REFERENCES lotteries(id) ON DELETE CASCADE
                );
            """)

    # ──────────────────────── lotteries ────────────────────────
    def create_lottery(self, name: str, positions: int, min_number: int, max_number: int) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO lotteries (name, positions, min_number, max_number) VALUES (?,?,?,?)",
                (name.strip(), positions, min_number, max_number)
            )
            return cur.lastrowid

    def get_lotteries(self) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT id, name, positions, min_number, max_number FROM lotteries ORDER BY name"
            ).fetchall()
        return [{"id": r[0], "name": r[1], "positions": r[2],
                 "min_number": r[3], "max_number": r[4]} for r in rows]

    def get_lottery(self, lottery_id: int) -> dict | None:
        with self._conn() as c:
            r = c.execute(
                "SELECT id, name, positions, min_number, max_number FROM lotteries WHERE id=?",
                (lottery_id,)
            ).fetchone()
        if not r:
            return None
        return {"id": r[0], "name": r[1], "positions": r[2],
                "min_number": r[3], "max_number": r[4]}

    def update_lottery(self, lottery_id: int, name: str, positions: int,
                       min_number: int, max_number: int):
        with self._conn() as c:
            c.execute(
                "UPDATE lotteries SET name=?, positions=?, min_number=?, max_number=? WHERE id=?",
                (name.strip(), positions, min_number, max_number, lottery_id)
            )

    def delete_lottery(self, lottery_id: int):
        with self._conn() as c:
            c.execute("DELETE FROM lotteries WHERE id=?", (lottery_id,))

    # ──────────────────────── draws ────────────────────────────
    def add_draw(self, lottery_id: int, numbers: list[int],
                 draw_date: str | None = None) -> int:
        if draw_date is None:
            draw_date = datetime.now().strftime("%Y-%m-%d")
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO draws (lottery_id, draw_date, numbers) VALUES (?,?,?)",
                (lottery_id, draw_date, json.dumps(numbers))
            )
            return cur.lastrowid

    def get_draws(self, lottery_id: int, limit: int | None = None) -> list[dict]:
        sql = ("SELECT id, lottery_id, draw_date, numbers, created_at "
               "FROM draws WHERE lottery_id=? ORDER BY draw_date DESC, id DESC")
        params: tuple = (lottery_id,)
        if limit:
            sql += " LIMIT ?"
            params = (lottery_id, limit)
        with self._conn() as c:
            rows = c.execute(sql, params).fetchall()
        return [{"id": r[0], "lottery_id": r[1], "draw_date": r[2],
                 "numbers": json.loads(r[3]), "created_at": r[4]} for r in rows]

    def get_all_numbers(self, lottery_id: int) -> list[list[int]]:
        """Devuelve sólo las listas de números ordenadas cronológicamente (ASC)."""
        with self._conn() as c:
            rows = c.execute(
                "SELECT numbers FROM draws WHERE lottery_id=? ORDER BY draw_date ASC, id ASC",
                (lottery_id,)
            ).fetchall()
        return [json.loads(r[0]) for r in rows]

    def delete_draw(self, draw_id: int):
        with self._conn() as c:
            c.execute("DELETE FROM draws WHERE id=?", (draw_id,))

    def draw_exists(self, lottery_id: int, numbers: list[int]) -> bool:
        """Verifica si una combinación exacta ya existe."""
        nums_json = json.dumps(sorted(numbers))
        with self._conn() as c:
            rows = c.execute(
                "SELECT numbers FROM draws WHERE lottery_id=?", (lottery_id,)
            ).fetchall()
        for r in rows:
            if sorted(json.loads(r[0])) == sorted(numbers):
                return True
        return False

    def get_draw_count(self, lottery_id: int) -> int:
        with self._conn() as c:
            return c.execute(
                "SELECT COUNT(*) FROM draws WHERE lottery_id=?", (lottery_id,)
            ).fetchone()[0]

    def import_draws_from_list(self, lottery_id: int,
                               draws_data: list[tuple[str, list[int]]]) -> int:
        """Importa una lista de (fecha, numeros). Devuelve cuántos se insertaron."""
        inserted = 0
        for date, numbers in draws_data:
            if not self.draw_exists(lottery_id, numbers):
                self.add_draw(lottery_id, numbers, date)
                inserted += 1
        return inserted
