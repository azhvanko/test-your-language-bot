import os.path
import re
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Sequence, Tuple, Union

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


def insert(table: str, columns: Tuple[str, ...], values: List[Sequence]) -> None:
    columns_list = ', '.join(columns)
    placeholders = ', '.join('?' * len(columns))
    _cursor.executemany(
        f'INSERT INTO {table} '
        f'({columns_list}) '
        f'VALUES ({placeholders})',
        values)
    _connection.commit()


def add_new_user(user_id: int, date: datetime, deep_link: Optional[str]) -> None:
    if deep_link is not None and _is_valid_deep_link(deep_link):
        user_role = _update_deep_link(user_id, date, deep_link)
    else:
        user_role = 'user'
    role_id = get_role_id(user_role)
    joined = _get_formatted_date(date)
    insert_user([(user_id, role_id, joined), ])


def execute_script(script: str) -> None:
    _cursor.executescript(script)
    _connection.commit()


def generate_questions_values(
        user_id: int,
        language_id: int,
        test_type_id: int,
        questions: List[Dict]
) -> List[Tuple]:
    values = []
    for question in questions:
        _question = normalize_question(question['question'])
        values.append(
            (
                user_id,
                language_id,
                test_type_id,
                _question,
                '\n'.join(answer.replace('\n', '').strip() for answer in question['answers']),
                len(question['answers']),
                question['answers'].index(question['right_answer']),
            )
        )
    return values


def get_admin_ids() -> List[int]:
    _cursor.execute(
        'SELECT id '
        'FROM users '
        'WHERE role_id = (SELECT id FROM roles WHERE role = "admin")'
    )
    return [int(i[0]) for i in _cursor.fetchall()]


def _get_formatted_date(date: datetime) -> str:
    return date.strftime("%Y-%m-%d %H:%M:%S")


def get_language_id(language: str, key: str = 'name') -> int:
    language = language.title() if key == 'name' else language.upper()
    _cursor.execute(
        f'SELECT id '
        f'FROM languages '
        f'WHERE {key} = "{language}"'
    )
    return int(_cursor.fetchone()[0])


def get_number_languages() -> int:
    _cursor.execute('SELECT count(*) '
                    'FROM languages')
    return int(_cursor.fetchone()[0])


def get_number_tables() -> int:
    _cursor.execute('SELECT count(*) '
                    'FROM sqlite_master '
                    'WHERE type = "table"')
    return int(_cursor.fetchone()[0])


def get_number_questions() -> int:
    _cursor.execute('SELECT count(*) '
                    'FROM questions')
    return int(_cursor.fetchone()[0])


def get_number_roles() -> int:
    _cursor.execute('SELECT count(*) '
                    'FROM roles')
    return int(_cursor.fetchone()[0])


def get_number_test_types() -> int:
    _cursor.execute('SELECT count(*) '
                    'FROM test_types')
    return int(_cursor.fetchone()[0])


def get_role_id(role: str) -> int:
    _cursor.execute(
        f'SELECT id '
        f'FROM roles '
        f'WHERE role = "{role}"'
    )
    return int(_cursor.fetchone()[0])


def get_user_role(user_id: int, key: str = 'role') -> Union[int, str]:
    if key == 'role':
        sql = (f'SELECT role '
               f'FROM roles '
               f'WHERE id = (SELECT role_id '
               f'            FROM users '
               f'            WHERE id = {user_id})')
    else:
        sql = (f'SELECT role_id '
               f'FROM users '
               f'WHERE id = {user_id}')
    _cursor.execute(sql)
    return _cursor.fetchone()[0]


def insert_questions(values: List[Tuple]) -> None:
    table = 'questions'
    columns = ('user_id', 'language_id', 'test_type_id', 'question',
               'answers', 'number_answers', 'right_answer')
    insert(table, columns, values)


def insert_user(values: List[Tuple]) -> None:
    table = 'users'
    columns = ('id', 'role_id', 'joined')
    insert(table, columns, values)


def is_new_user(user_id: int) -> bool:
    _cursor.execute(
        f'SELECT count(*) '
        f'FROM users '
        f'WHERE id = {user_id}'
    )
    return not bool(_cursor.fetchone()[0])


def _is_valid_deep_link(deep_link: str) -> bool:
    _cursor.execute(
        f'SELECT count(*) '
        f'FROM deep_links '
        f'WHERE link = "{deep_link}" '
        f'AND user_id is NULL'
    )
    return bool(_cursor.fetchone()[0])


def normalize_question(question: str) -> str:
    pattern_underscore = r'(?<!_)(?:_{1,2}|_{4,})(?!_)'
    pattern_space = r'\s{2,}'
    question = re.sub(pattern_underscore, '___', question)
    question = re.sub(pattern_space, ' ', question)
    return question.strip()


def _register_deep_link(user_id: int, deep_link: str, role: str) -> None:
    table = 'deep_links'
    columns = ('link', 'creator_id', 'role',)
    values = [(deep_link, user_id, role)]
    insert(table, columns, values)


def _update_deep_link(user_id: int, date: datetime, deep_link: str) -> str:
    date = _get_formatted_date(date)
    _cursor.execute(
        f'UPDATE deep_links '
        f'SET user_id = {user_id}, '
        f'    joined = "{date}" '
        f'WHERE link = "{deep_link}"'
    )
    _cursor.execute(
        f'SELECT role '
        f'FROM deep_links '
        f'WHERE link = "{deep_link}"'
    )
    return _cursor.fetchone()[0]


def update_user_role(user_id: int, date: datetime, deep_link: str) -> None:
    if _is_valid_deep_link(deep_link):
        new_user_role = _update_deep_link(user_id, date, deep_link)
        user_role = get_user_role(user_id)
        if user_role != 'admin':
            role_id = get_role_id(new_user_role)
            _cursor.execute(
                f'UPDATE users '
                f'SET role_id = {role_id} '
                f'WHERE id = {user_id}'
            )
            _connection.commit()
