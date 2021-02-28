from datetime import datetime
from uuid import uuid4

import pytest

from core.db import (
    add_new_user,
    delete_questions,
    _generate_language_test,
    generate_questions_values,
    get_all_languages,
    get_all_questions,
    get_all_test_types,
    get_current_languages,
    get_language_id,
    get_language_test,
    get_number_languages,
    get_number_test_types,
    get_role_id,
    get_test_type_id,
    get_test_types,
    _get_user_answers,
    get_user_role,
    insert_questions,
    is_new_user,
    is_supported_language,
    is_supported_test_type,
    _is_valid_deep_link,
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


def test_delete_questions():
    new_question = {
        'language': 'ENG',
        'test_type': 1,
        'questions': [
            {
                'question': 'Jack is in his garage. He must ___ his car.',
                'answers': ['be repairing', 'have been repairing', 'have repaired', 'repair'],
                'right_answer': 'be repairing'
            },
        ]
    }
    language_id = get_language_id(new_question['language'], 'code')
    values = generate_questions_values(
        1, language_id, new_question['language'], new_question['questions']
    )
    question = new_question['questions'][0]['question']
    insert_questions(values)
    all_questions = get_all_questions(1)
    assert question in all_questions
    delete_questions([all_questions[question], ])
    assert question not in get_all_questions(1)


@pytest.mark.parametrize(
    'ids, eq, result',
    (
        (
            [1, 2],
            True,
            [
                (1, "The moon wouldn't ___ so beautiful.", 'have looked\nhave been looking\nlook\nam looking', 0),
                (2, 'He must ___ all along.', 'have been knowing\nare knowing\nknow\nhave known', 3),
            ],
        ),
        (
            [1, 2],
            False,
            [
                (3, 'They seem ___ by some kind of an instrument.', 'to make\nto have been made\nto have made\nto be made', 1),
            ],
        ),
    )
)
def test_generate_language_test(ids, eq, result):
    language_test = _generate_language_test(10, 1, 4, 10, ids, eq)
    assert sorted(language_test, key=lambda x: x[0]) == result


def test_get_all_languages():
    assert len(get_all_languages()) == get_number_languages()


def test_get_all_questions():
    assert get_all_questions(1)


@pytest.mark.parametrize(
    'flag, _type',
    (
        (True, int, ),
        (False, tuple, ),
    )
)
def test_get_all_test_types(flag, _type):
    result = get_all_test_types(flag)
    assert all(isinstance(i, _type) for i in result)
    assert len(result) == get_number_test_types()


def test_get_current_languages():
    assert get_current_languages() == ['English', ]


@pytest.mark.parametrize(
    'language, key, result',
    (
        ('Belarusian', 'name', 1),
        ('BEL', 'code', 1),
    )
)
def test_get_language_id(language, key, result):
    assert get_language_id(language, key) == result


def test_get_language_test():
    language_test = get_language_test(1, 10, 1, 4, 10)
    result = [
        (1, "The moon wouldn't ___ so beautiful.", 'have looked\nhave been looking\nlook\nam looking', 0),
        (2, 'He must ___ all along.', 'have been knowing\nare knowing\nknow\nhave known', 3),
        (3, 'They seem ___ by some kind of an instrument.', 'to make\nto have been made\nto have made\nto be made', 1),
    ]
    assert sorted(language_test, key=lambda x: x[0]) == result


def test_get_role_id():
    assert all(
        get_role_id(role) == index
        for index, role in enumerate(('admin', 'test_creator', 'user'), start=1)
    )


def test_get_test_type_id():
    result = get_test_type_id('Тест по грамматике.')
    assert result == 1


def test_get_test_types():
    result = ['Тест по грамматике.', 'Тест по существительным.', ]
    assert get_test_types('English') == result
    assert get_test_types(get_language_id('English')) == result


@pytest.mark.parametrize(
    'user_id, language_id, test_type_id, number_answers, eq, result',
    (
        (1, 10, 1, 4, True, [1, 2, ]),
        (1, 10, 1, 4, False, [3, ]),
        (2, 10, 1, 4, True, []),
        (2, 10, 1, 4, False, [1, 2, 3, ]),
    )
)
def test_get_user_answers(
        user_id, language_id, test_type_id, number_answers, eq, result
):
    answers = _get_user_answers(user_id, language_id, test_type_id, number_answers, eq)
    assert answers == result


def test_get_user_role():
    assert get_user_role(1, 'role') == 'admin'
    assert get_user_role(1, 'id') == 1


def test_is_new_user():
    assert not all(is_new_user(i) for i in range(1, 4))
    assert is_new_user(1234567890)


@pytest.mark.parametrize(
    'language, key, result',
    (
        ('English', 'name', True),
        ('ENG', 'code', True),
        ('English', 'code', False),
        ('ENG', 'name', False),
        ('Latin', 'name', False),
    )
)
def test_is_supported_language(language, key, result):
    assert is_supported_language(language, key) == result


@pytest.mark.parametrize(
    'test_type, result',
    (
        ('Тест по грамматике.', True),
        ('тест по грамматике.', True),
        ('1', False),
        ('Грамматика', False),
    )
)
def test_is_supported_test_type(test_type, result):
    assert is_supported_test_type(test_type) == result


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


def test_update_user_role():
    user_id = 101
    add_new_user(user_id, datetime.now(), None)
    assert get_user_role(user_id) == 'user'
    deep_link = str(uuid4())
    _register_deep_link(1, deep_link, 'test_creator')
    update_user_role(user_id, datetime.now(), deep_link)
    assert get_user_role(user_id) == 'test_creator'
    assert not _is_valid_deep_link(deep_link)
