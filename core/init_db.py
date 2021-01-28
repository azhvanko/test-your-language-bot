import json
import os.path
from typing import List, Sequence, Tuple

from .config import ADMINS, INIT_DATA_DIR
from .db import (
    execute_script,
    generate_questions_values,
    get_admin_ids,
    get_language_id,
    get_number_tables,
    get_role_id,
    insert,
    insert_questions,
    insert_user
)


def check_db_exists(admins: Sequence = ADMINS, path: str = INIT_DATA_DIR) -> None:
    """
    Checks if db is initialized, if not, initializes.
    """
    if get_number_tables() > 0:
        return
    _init_db(path)
    _insert_data(admins, path)


def _init_db(script_path: str = INIT_DATA_DIR) -> None:
    """Initializes db."""
    _script_path = os.path.join(script_path, 'create_db.sql')
    with open(_script_path, mode='r') as file:
        script = file.read()
    execute_script(script)


def _insert_data(admins: Sequence, path: str = INIT_DATA_DIR) -> None:
    _insert_languages_list(path)
    _insert_tests_types(path)
    _insert_roles(path)
    _add_admins(admins)
    files = _get_files_list(path)
    values = _get_values(files)
    insert_questions(values)


def _insert_languages_list(path: str = INIT_DATA_DIR) -> None:
    file_path = os.path.join(path, 'languages')
    with open(file_path, mode='r', encoding='utf-8') as file:
        languages_list = [line.replace('\n', '').split(' - ') for line in file]
    columns = ('code', 'name',)
    insert('languages', columns, languages_list)


def _insert_tests_types(path: str = INIT_DATA_DIR) -> None:
    file_path = os.path.join(path, 'test_types')
    with open(file_path, mode='r', encoding='utf-8') as file:
        test_types_list = [(line.replace('\n', ''),) for line in file]
    columns = ('type',)
    insert('test_types', columns, test_types_list)


def _insert_roles(path: str = INIT_DATA_DIR) -> None:
    file_path = os.path.join(path, 'roles')
    with open(file_path, mode='r', encoding='utf-8') as file:
        roles = [(line.replace('\n', ''), ) for line in file]
    columns = ('role',)
    insert('roles', columns, roles)


def _add_admins(admins: Sequence = ADMINS) -> None:
    role_id = get_role_id('admin')
    joined = '2021-01-01 12:00:00'
    values = [(user_id, role_id, joined) for user_id in admins]
    insert_user(values)


def _get_files_list(path: str = INIT_DATA_DIR) -> List[str]:
    return [
        file
        for file in os.listdir(path)
        if file.startswith('language_test_')
    ]


def _get_values(files: List[str], path: str = INIT_DATA_DIR) -> List[Tuple]:
    admin_id = get_admin_ids()[0]
    values = []
    for file in files:
        file_path = os.path.join(path, file)
        with open(file_path, mode='r', encoding='utf-8') as test:
            data = json.loads(test.read())
        language_id = get_language_id(data['language'], 'code')
        test_type_id = int(data['test_type'])
        _values = generate_questions_values(
            admin_id, language_id, test_type_id, data['questions']
        )
        values.extend(_values)
    return values
