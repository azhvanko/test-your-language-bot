from datetime import datetime
from unittest.mock import Mock

import pytest

from core.db import (
    get_formatted_languages_list,
    get_formatted_test_types_list,
    get_user_role
)
from core.dispatcher import UnclosedSessionError
from core.types import Answer, UserSession


@pytest.mark.parametrize(
    'text, result',
    (
        ('/start', True),
        ('/begin_test', True),
        ('start', False),
        ('12345', False),
        ('qwerty/start', False),
    )
)
def test_is_bot_command(dispatcher, text, result):
    assert dispatcher._is_bot_command(text) == result


@pytest.mark.parametrize(
    'command, result',
    (
        ('/start', ('start', None)),
        ('/begin_test', ('begin_test', None)),
        ('/start 2aefdcc2-5c09-4e29-bdea', ('start', None)),
        ('/start 2aefdcc2_5c09_4e29_bdea_ee61fdc01f23', ('start', None)),
        (
            '/start 2aefdcc2-5c09-4e29-bdea-ee61fdc01f23',
            ('start', '2aefdcc2-5c09-4e29-bdea-ee61fdc01f23')
        ),
    )
)
def test_get_bot_command(dispatcher, command, result):
    assert dispatcher._get_bot_command(command) == result


@pytest.mark.parametrize(
    'alias',
    (
        'user_session_handler',
    )
)
def test_get_handler(dispatcher, user_session_handler, alias):
    assert dispatcher._get_handler(alias) == user_session_handler


@pytest.mark.parametrize(
    'command',
    (
        'start',
        'reset',
    )
)
@pytest.mark.parametrize(
    'user_id',
    (
        1,
        2,
        3,
    )
)
def test_handle_start_commands(dispatcher, command, user_id):
    role = get_user_role(user_id)
    result = dispatcher._handle_start_commands(user_id, command, datetime.now(), None)
    assert isinstance(result, Answer)
    assert result.text == dispatcher._get_start_message(command, role).text


@pytest.mark.parametrize(
    'command',
    (
        'languages_list',
        'test_types_list',
    )
)
@pytest.mark.parametrize(
    'user_id',
    (
        1,
        2,
        3,
    )
)
def test_handle_information_commands(dispatcher, command, user_id):
    role = get_user_role(user_id)
    if role == 'user':
        text = dispatcher._get_default_answer('unsupported_command')
    else:
        if command == 'languages_list':
            text = get_formatted_languages_list()
        else:
            text = get_formatted_test_types_list()
    result = dispatcher._handle_information_commands(user_id, command)
    assert isinstance(result, Answer)
    assert result.text == text


@pytest.mark.parametrize(
    'command',
    (
        'create_deep_link',
    )
)
@pytest.mark.parametrize(
    'user_id',
    (
        2,
        3,
    )
)
def test_handle_admin_commands(dispatcher, command, user_id):
    role = get_user_role(user_id)
    if role != 'admin':
        text = dispatcher._get_default_answer('unsupported_command')
    else:
        assert False
    result = dispatcher._handle_admin_commands(user_id, command)
    assert isinstance(result, Answer)
    assert result.text == text


@pytest.mark.parametrize(
    'user_id',
    (
        1,
        2,
        3,
    )
)
@pytest.mark.parametrize(
    'text',
    (
        'create_deep_link',
        'start',
        'begin_test',
        '1'
    )
)
def test_handle_text(dispatcher, user_id, text):
    answer = dispatcher._handle_text(user_id, text)
    assert isinstance(answer, Answer)
    assert answer.text == dispatcher._get_default_answer('invalid_message')


@pytest.mark.parametrize(
    'user_id, date',
    (
        (3, datetime.now()),
    )
)
def test_handle_user_commands(dispatcher, user_session_handler, user_id, date):
    answer = dispatcher._handle_user_commands(user_id, date)
    func = user_session_handler._functions_map['select_language']
    _answer = func(Mock, None)
    assert isinstance(answer, Answer)
    assert answer.text == _answer.text

    dispatcher.close_session(user_id)


@pytest.mark.parametrize(
    'user_id, date',
    (
        (1, datetime.now()),
        (2, datetime.now()),
        (3, datetime.now()),
    )
)
def test_create_session(dispatcher, user_session_handler, user_id, date):
    session = dispatcher._create_session(user_id, date, user_session_handler)
    assert user_id in dispatcher._sessions
    assert isinstance(session, UserSession)

    dispatcher.close_session(user_id)


@pytest.mark.parametrize(
    'user_id, date',
    (
        (1, datetime.now()),
        (2, datetime.now()),
        (3, datetime.now()),
    )
)
def test_create_session_error(dispatcher, user_session_handler, user_id, date):
    _ = dispatcher._create_session(user_id, date, user_session_handler)
    with pytest.raises(UnclosedSessionError):
        _ = dispatcher._create_session(user_id, date, user_session_handler)

    dispatcher.close_session(user_id)


@pytest.mark.parametrize(
    'user_id, date',
    (
        (1, datetime.now()),
        (2, datetime.now()),
        (3, datetime.now()),
    )
)
def test_close_session(dispatcher, user_id, date):
    _ = dispatcher._handle_user_commands(user_id, date)
    assert user_id in dispatcher._sessions

    dispatcher.close_session(user_id)
    assert user_id not in dispatcher._sessions
