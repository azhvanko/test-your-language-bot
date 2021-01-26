import os.path
import sqlite3
from typing import List, Optional, Tuple

from .config import DB_DIR


_connection: Optional[sqlite3.Connection] = None
_cursor: Optional[sqlite3.Cursor] = None


def create_connection(db_name: str, db_path: str = DB_DIR) -> None:
    global _connection, _cursor
    if db_name == ':memory:':
        db_path = db_name
    else:
        db_path = os.path.join(db_path, db_name)
    _connection = sqlite3.connect(db_path)
    _cursor = _connection.cursor()


def close_connection():
    _connection.close()


def insert(table: str, columns: Tuple[str, ...], values: List[Tuple]) -> None:
    columns_list = ', '.join(columns)
    placeholders = ', '.join('?' * len(columns))
    _cursor.executemany(
        f'INSERT INTO {table} '
        f'({columns_list}) '
        f'VALUES ({placeholders})',
        values)
    _connection.commit()


def execute_script(script: str) -> None:
    _cursor.executescript(script)
    _connection.commit()


def get_number_tables() -> int:
    _cursor.execute('SELECT count(*) '
                    'FROM sqlite_master '
                    'WHERE type = "table"')
    return int(_cursor.fetchone()[0])
