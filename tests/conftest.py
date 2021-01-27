import pytest

from core.db import (
    create_connection,
    close_connection,
    get_role_id,
    _insert_user
)
from core.dispatcher import SessionsDispatcher
from core.init_db import (
    _init_db,
    _insert_data
)


def _insert_test_users() -> None:
    users = [
        (index, get_role_id(role), '2021-01-01 12:00:00')
        for index, role in enumerate(('admin', 'test_creator', 'user'), start=1)
    ]
    _insert_user(users)


@pytest.fixture(scope='session', autouse=True)
def db(tmpdir_factory):
    temp_dir = tmpdir_factory.mktemp('temp')
    create_connection('test_db', temp_dir)
    _init_db()
    _insert_data()
    _insert_test_users()
    yield
    close_connection()


@pytest.fixture(scope='session')
def dispatcher():
    return SessionsDispatcher()
