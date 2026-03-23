from __future__ import annotations

import sqlite3
from pathlib import Path

from catalyst.storage.schema import INDEX_STATEMENTS, SCHEMA_STATEMENTS


class SQLiteStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            for statement in SCHEMA_STATEMENTS:
                conn.execute(statement)
            for statement in INDEX_STATEMENTS:
                conn.execute(statement)
            conn.commit()
