import random
import string

import pytest

from core.db import (
    create_connection,
    close_connection,
    insert_user_answers
)
from core.dispatcher import SessionsDispatcher
from core.init_db import (
    _init_db,
    _insert_data
)
from core.handlers import (
    user_session_handler as _user_session_handler,
    language_test_creator_session_handler as _language_test_creator_session_handler
)


def _insert_test_data() -> None:
    _init_db()
    _insert_data([1, ])


def _insert_user_answers() -> None:
    values = [
        (1, 1, 0, '2021-01-01 12:00:00'),  # right answer
        (1, 2, 3, '2021-01-01 12:00:00'),  # right answer
        (1, 3, 0, '2021-01-01 12:00:00'),  # wrong answer
        (2, 1, 1, '2021-01-01 12:00:00'),  # wrong answer
        (2, 2, 0, '2021-01-01 12:00:00'),  # wrong answer
        (2, 3, 0, '2021-01-01 12:00:00'),  # wrong answer
    ]
    insert_user_answers(values)


@pytest.fixture(scope='session', autouse=True)
def db(tmpdir_factory):
    temp_dir = tmpdir_factory.mktemp('temp')
    create_connection('test_db', temp_dir)
    _insert_test_data()
    _insert_user_answers()
    yield
    close_connection()


@pytest.fixture(scope='session', autouse=True)
def dispatcher():
    sd = SessionsDispatcher()
    sd.register_handlers(
        _user_session_handler,
        _language_test_creator_session_handler,
    )
    return sd


@pytest.fixture(scope='session', autouse=True)
def user_session_handler():
    return _user_session_handler


@pytest.fixture(scope='session', autouse=True)
def language_test_creator_session_handler():
    return _language_test_creator_session_handler


@pytest.fixture(scope='function')
def random_language_test():
    question = f'{_get_random_ascii_string()} ___ {_get_random_ascii_string()}.'
    language_test = {
        'language': 'ENG',
        'test_type': 1,
        'questions': [
            {
                'question': question,
                'answers': ['answer1', 'answer2', 'answer3', 'answer4'],
                'right_answer': 'answer1'
            },
        ]
    }
    return language_test


def _get_random_ascii_string(length: int = 16) -> str:
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))
