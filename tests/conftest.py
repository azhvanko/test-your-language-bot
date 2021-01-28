import pytest

from core.db import (
    create_connection,
    close_connection
)
from core.dispatcher import SessionsDispatcher
from core.init_db import (
    _init_db,
    _insert_data
)


def _insert_test_data() -> None:
    _init_db()
    _insert_data([1, ])


@pytest.fixture(scope='session', autouse=True)
def db(tmpdir_factory):
    temp_dir = tmpdir_factory.mktemp('temp')
    create_connection('test_db', temp_dir)
    _insert_test_data()
    yield
    close_connection()


@pytest.fixture(scope='session')
def dispatcher():
    return SessionsDispatcher()
