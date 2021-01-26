import pytest

from core.db import create_connection, close_connection
from core.dispatcher import SessionsDispatcher


@pytest.fixture(scope='session', autouse=True)
def db(tmpdir_factory):
    temp_dir = tmpdir_factory.mktemp('temp')
    create_connection('test_db', temp_dir)
    yield
    close_connection()


@pytest.fixture(scope='session')
def dispatcher():
    return SessionsDispatcher()
