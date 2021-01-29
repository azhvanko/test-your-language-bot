from datetime import datetime
from uuid import uuid4

import pytest

from core.db import (
    add_new_user,
    _get_all_test_types,
    get_language_id,
    _get_languages,
    get_number_languages,
    get_number_test_types,
    get_role_id,
    get_user_role,
    is_new_user,
    normalize_question,
    _register_deep_link,
    update_user_role
)


@pytest.mark.parametrize(
    'user_id, deep_link, final_role',
    (
        (2, str(uuid4()), 'test_creator'),
        (3, None, 'user'),
    )
)
def test_add_new_user(user_id, deep_link, final_role):
    if deep_link is not None:
        _register_deep_link(1, deep_link, 'test_creator')
    add_new_user(user_id, datetime.now(), deep_link)
    assert get_user_role(user_id) == final_role


def test_update_user_role():
    user_id = 3
    deep_link = str(uuid4())
    assert get_user_role(user_id) == 'user'
    _register_deep_link(1, deep_link, 'test_creator')
    update_user_role(user_id, datetime.now(), deep_link)
    assert get_user_role(user_id) == 'test_creator'


@pytest.mark.parametrize(
    'flag, _type',
    (
        (True, int, ),
        (False, tuple, ),
    )
)
def test_get_all_test_types(flag, _type):
    result = _get_all_test_types(flag)
    assert all(isinstance(i, _type) for i in result)
    assert len(result) == get_number_test_types()


@pytest.mark.parametrize(
    'language, key, result',
    (
        ('Belarusian', 'name', 1),
        ('BEL', 'code', 1),
    )
)
def test_get_language_id(language, key, result):
    assert get_language_id(language, key) == result


def test_get_languages():
    assert len(_get_languages()) == get_number_languages()


def test_get_role_id():
    assert all(
        get_role_id(role) == index
        for index, role in enumerate(('admin', 'test_creator', 'user'), start=1)
    )


def test_get_user_role():
    assert get_user_role(1, 'role') == 'admin'
    assert get_user_role(1, 'id') == 1


def test_is_new_user():
    assert not all(is_new_user(i) for i in range(1, 4))
    assert is_new_user(1234567890)


@pytest.mark.parametrize(
    'question, result',
    (
        ('Test  question ', 'Test question'),
        (' Test    question ', 'Test question'),
        ('He must __ all along. ', 'He must ___ all along.'),
        ('He must  ____  all along. ', 'He must ___ all along.'),
    )
)
def test_normalize_question(question, result):
    assert normalize_question(question) == result
