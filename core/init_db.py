import os.path

from .config import INIT_DATA_DIR
from .db import (
    execute_script,
    insert
)


def _init_db(script_path: str = INIT_DATA_DIR) -> None:
    """Initializes db."""
    _script_path = os.path.join(script_path, 'create_db.sql')
    with open(_script_path, mode='r') as file:
        script = file.read()
    execute_script(script)


def _insert_data() -> None:
    _insert_languages_list()
    _insert_tests_types()
    _insert_roles()


def _insert_languages_list() -> None:
    file_path = os.path.join(INIT_DATA_DIR, 'languages')
    with open(file_path, mode='r', encoding='utf-8') as file:
        languages_list = [line.replace('\n', '').split(' - ') for line in file]
    columns = ('code', 'name',)
    insert('languages', columns, languages_list)


def _insert_tests_types() -> None:
    file_path = os.path.join(INIT_DATA_DIR, 'test_types')
    with open(file_path, mode='r', encoding='utf-8') as file:
        test_types_list = [(line.replace('\n', ''),) for line in file]
    columns = ('type',)
    insert('test_types', columns, test_types_list)


def _insert_roles() -> None:
    file_path = os.path.join(INIT_DATA_DIR, 'roles')
    with open(file_path, mode='r', encoding='utf-8') as file:
        roles = [(line.replace('\n', ''), ) for line in file]
    columns = ('role',)
    insert('roles', columns, roles)
