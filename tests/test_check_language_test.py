import os

import pytest

from core.check_language_test import (
    _check_duplicate_questions,
    _check_keys,
    _check_keys_type,
    _check_language,
    check_language_test,
    _check_number_answers,
    _check_right_answer,
    _check_test_type,
    _check_questions,
    language_test_keys,
    question_keys
)
from core.config import INIT_DATA_DIR
from core.exceptions import *


@pytest.fixture(scope='session')
def language_test():
    with open(os.path.join(INIT_DATA_DIR, 'language_test_1.txt'), 'rb') as file:
        return check_language_test(file, False)


def test_check_duplicate_questions(language_test):
    with pytest.raises(DuplicateQuestionError):
        _check_duplicate_questions(language_test['questions'])


@pytest.mark.parametrize(
    'data, keys',
    (
        (('question', '1', 1, 'testtype', 'id'), language_test_keys),
        (('questions', '1', 1, 'answer', 'id', 'right'), question_keys),
    )
)
def test_check_keys(data, keys):
    with pytest.raises(KeyMissingError):
        for key in data:
            _check_keys({key: ''}, keys)


@pytest.mark.parametrize(
    'key, values',
    (
        ('question', (1, [], {}, True)),
        ('answers', (1, 'answers', {}, True)),
        ('right_answer', (1, [], {}, True)),
    )
)
def test_check_keys_type(key, values):
    with pytest.raises(KeyTypeError):
        for value in values:
            _check_keys_type({key: value}, question_keys)


@pytest.mark.parametrize(
    'code',
    (
        'EN', 'ABC', 'English'
    )
)
def test_check_language(code):
    with pytest.raises(LanguageTypeError):
        _check_language(code)


@pytest.mark.parametrize(
    'answers',
    (
        [0, ],
        [0 for _ in range(9)],
    )
)
def test_check_number_answers(answers):
    print(answers, type(answers))
    with pytest.raises(NumberAnswersError):
        _check_number_answers({'question': '', 'answers': answers})


def test_check_questions(language_test):
    with pytest.raises(DuplicateQuestionError):
        _check_questions(language_test['questions'], True)


@pytest.mark.parametrize(
    'test_types',
    (
        ('test', '1.0', '5.5', 12345, -1, 100),
    )
)
def test_check_test_type(test_types):
    with pytest.raises(LanguageTestTypeError):
        for test_type in test_types:
            _check_test_type(test_type)


@pytest.mark.parametrize(
    'right_answer, answers',
    (
        ('answer0', ['answer1', 'answer2', 'answer3', 'answer4', ]),
    )
)
def test_check_right_answer(right_answer, answers):
    with pytest.raises(RightAnswerError):
        _check_right_answer(
            {'question': '', 'right_answer': right_answer, 'answers': answers}
        )
