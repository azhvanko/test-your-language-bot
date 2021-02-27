import os.path
import re
import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Sequence, Tuple, Union

from core.config import BOT_NAME, DB_DIR
from core.types import LanguageTest


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


def create_deep_link(user_id: int, role: str = 'test_creator') -> str:
    deep_link = str(uuid.uuid4())
    _register_deep_link(user_id, deep_link, role)
    return f'https://t.me/{BOT_NAME}?start={deep_link}'


def execute_script(script: str) -> None:
    _cursor.executescript(script)
    _connection.commit()


def generate_answer_values(
        user_id: int, language_test: LanguageTest
) -> List[Tuple]:
    values = [
        (user_id,
         language_test.questions[index].question_id,
         language_test.questions[index].get_answer_index(answer),
         _get_formatted_date(datetime.now()))
        for index, answer in enumerate(language_test.user_answers)
    ]
    return values


def _generate_language_test(
        language_id: int,
        test_type_id: int,
        number_answers: int,
        limit: int,
        question_ids: List[Union[int, str]],
        eq: bool
) -> List[Tuple]:
    question_ids = ', '.join(str(i) for i in question_ids)
    operator = 'IN' if eq else 'NOT IN'
    _cursor.execute(
        f'SELECT '
        f'    id, '
        f'    question, '
        f'    answers, '
        f'    right_answer '
        f'FROM '
        f'    questions '
        f'WHERE '
        f'    language_id = {language_id} '
        f'    AND test_type_id = {test_type_id} '
        f'    AND number_answers = {number_answers} '
        f'    AND id {operator} ({question_ids})'
        f'ORDER BY RANDOM() '
        f'LIMIT {limit}'
    )
    return [i for i in _cursor.fetchall()]


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
                '\n'.join(answer.replace('\n', '').strip()
                          for answer in question['answers']),
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


def get_all_languages(key: Optional[str] = None) -> List[Tuple]:
    key = key or 'id, code, name'
    _cursor.execute(
        f'SELECT {key} '
        f'FROM languages'
    )
    return _cursor.fetchall()


def get_all_questions(user_id: int) -> Dict[str, int]:
    condition = f'WHERE user_id = {user_id}' if user_id > 0 else ''
    _cursor.execute(
        f'SELECT question, id '
        f'FROM questions '
        f'{condition}'
    )
    return {i[0]: i[1] for i in _cursor.fetchall()}


def get_all_test_types(ids: bool = False) -> List[Union[int, Tuple]]:
    _cursor.execute(
        'SELECT id, type '
        'FROM test_types'
    )
    if ids:
        return [i[0] for i in _cursor.fetchall()]
    return _cursor.fetchall()


def get_current_languages() -> List[str]:
    _cursor.execute(
        f'SELECT name '
        f'FROM languages '
        f'WHERE id IN (SELECT DISTINCT language_id FROM questions)'
    )
    current_languages = [i[0] for i in _cursor.fetchall()]
    return sorted(current_languages)


def _get_formatted_date(date: datetime) -> str:
    return date.strftime("%Y-%m-%d %H:%M:%S")


def get_formatted_languages_list() -> str:
    all_languages = get_all_languages()
    return '\n'.join(f'{code} - {name}' for _, code, name in all_languages)


def get_formatted_test_types_list() -> str:
    all_test_types = get_all_test_types()
    return '\n'.join(f'{_id}. {_type}' for _id, _type in all_test_types)


def get_language_id(language: str, key: str = 'name') -> int:
    language = language.capitalize() if key == 'name' else language.upper()
    _cursor.execute(
        f'SELECT id '
        f'FROM languages '
        f'WHERE {key} = "{language}"'
    )
    return int(_cursor.fetchone()[0])


def get_language_test(
        user_id: int,
        language_id: int,
        test_type_id: int,
        number_answers: int,
        limit: int
) -> List[Tuple]:
    last_right_questions = _get_user_answers(
        user_id, language_id, test_type_id, number_answers, True
    )
    questions = _generate_language_test(
        language_id, test_type_id, number_answers, limit, last_right_questions, False
    )
    if not questions or len(questions) < limit:
        limit = limit - len(questions)
        _questions = _generate_language_test(
            language_id, test_type_id, number_answers, limit, last_right_questions, True
        )
        questions.extend(_questions)
    return questions


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


def get_test_type_id(test_type: str) -> int:
    _cursor.execute(
        f'SELECT id '
        f'FROM test_types '
        f'WHERE type = "{test_type}"'
    )
    return int(_cursor.fetchone()[0])


def get_test_types(language: Union[int, str]) -> List[str]:
    if isinstance(language, str):
        language = get_language_id(language)
    _cursor.execute(
        f'SELECT type '
        f'FROM test_types '
        f'WHERE id IN (SELECT DISTINCT test_type_id '
        f'             FROM questions '
        f'             WHERE language_id = {language})'
    )
    return [i[0] for i in _cursor.fetchall()]


def _get_user_answers(
        user_id: int,
        language_id: int,
        test_type_id: int,
        number_answers: int,
        eq: bool
) -> List[int]:
    operator = '=' if eq else '!='
    _cursor.execute(
        f'SELECT'
        f'    q.id '
        f'FROM '
        f'    questions q, '
        f'    (SELECT '
        f'        tr.question_id, '
        f'        tr.answer '
        f'    FROM '
        f'        test_results tr '
        f'    WHERE '
        f'        user_id = {user_id} '
        f'        AND tr.date = (SELECT MAX(date) '
        f'                       FROM test_results '
        f'                       WHERE question_id = tr.question_id) '
        f'    ) ltr '
        f'WHERE '
        f'    q.id = ltr.question_id '
        f'    AND q.language_id = {language_id} '
        f'    AND q.test_type_id = {test_type_id} '
        f'    AND q.number_answers = {number_answers} '
        f'    AND q.right_answer {operator} ltr.answer'
    )
    return [int(i[0]) for i in _cursor.fetchall()]


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


def insert_user_answers(values: List[Tuple]) -> None:
    table = 'test_results'
    columns = ('user_id', 'question_id', 'answer', 'date')
    insert(table, columns, values)


def is_new_user(user_id: int) -> bool:
    _cursor.execute(
        f'SELECT count(*) '
        f'FROM users '
        f'WHERE id = {user_id}'
    )
    return not bool(_cursor.fetchone()[0])


def is_supported_language(language: str, key: str = 'name') -> bool:
    _cursor.execute(
        f'SELECT {key} '
        f'FROM languages '
        f'WHERE id in (SELECT DISTINCT language_id FROM questions)'
    )
    languages = {i[0].upper() for i in _cursor.fetchall()}
    return language.upper().strip() in languages


def is_supported_test_type(test_type: str) -> bool:
    _cursor.execute(
        'SELECT type '
        'FROM test_types'
    )
    test_types = {i[0] for i in _cursor.fetchall()}
    return test_type.capitalize().strip() in test_types


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
