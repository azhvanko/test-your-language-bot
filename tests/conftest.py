import pytest

from core.dispatcher import SessionsDispatcher


@pytest.fixture(scope='session')
def dispatcher():
    return SessionsDispatcher()
