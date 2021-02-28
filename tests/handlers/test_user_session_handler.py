from datetime import datetime

import pytest
from aiogram.types import ReplyKeyboardMarkup

from core.handlers import SessionHandler
from core.handlers.user_session_handler import _get_fmt_wrong_answers
from core.types import (
    Answer,
    CloseSession,
    UserSession
)


answers = {
    'select_language': {
        None: 'Выберите один из доступных языков.',
        'ENG': 'Вы прислали неподдерживаемый язык.\nВыберите один из доступных языков.',
        '1': 'Вы прислали неподдерживаемый язык.\nВыберите один из доступных языков.',
    },
    'select_test_type': {
        None: 'Выберите один из доступных типов теста.',
        'Грамматика': 'Вы прислали неверный тип теста\nВыберите один из доступных типов теста.',
        '1': 'Вы прислали неверный тип теста\nВыберите один из доступных типов теста.',
    }
}


@pytest.fixture(scope='function')
def user_session():
    return UserSession(
        'user_session_handler',
        1,
        datetime.now()
    )


def _update_step(
        user_session_handler: SessionHandler, user_session: UserSession, step: int
) -> UserSession:
    steps = ('English', 'Тест по грамматике.')
    for i in range(step):
        _ = user_session_handler.handle_session(user_session, steps[i])
    return user_session


@pytest.mark.parametrize(
    'values',
    [(key, value) for key, value in answers['select_language'].items()]
)
def _test_select_language(user_session_handler, user_session, values):
    message, result = values
    answer = user_session_handler.handle_session(user_session, message)
    assert isinstance(answer, Answer)
    assert answer.text == result
    assert isinstance(answer.keyboard, ReplyKeyboardMarkup)


@pytest.mark.parametrize(
    'values',
    [(key, value) for key, value in answers['select_test_type'].items()]
)
def _test_select_test_type(user_session_handler, user_session, values):
    user_session = _update_step(user_session_handler, user_session, 1)
    message, result = values
    answer = user_session_handler.handle_session(user_session, message)
    assert isinstance(answer, Answer)
    assert answer.text == result
    assert isinstance(answer.keyboard, ReplyKeyboardMarkup)


def test_select_language(user_session_handler, user_session):
    answer = user_session_handler.handle_session(user_session, 'English')
    assert isinstance(answer, Answer)
    assert answer.text == 'Выберите один из доступных типов теста.'
    assert isinstance(answer.keyboard, ReplyKeyboardMarkup)


def test_select_test_type(user_session_handler, user_session):
    user_session = _update_step(user_session_handler, user_session, 1)
    answers = user_session_handler.handle_session(user_session, 'Тест по грамматике.')
    assert isinstance(answers, tuple)
    assert len(answers) == 2
    assert all(isinstance(answer, Answer) for answer in answers)


def test_generate_language_test(user_session_handler, user_session):
    user_session = _update_step(user_session_handler, user_session, 2)
    answers = user_session_handler.handle_session(user_session, None)
    assert isinstance(answers, tuple)
    assert len(answers) == 2
    assert all(isinstance(answer, Answer) for answer in answers)


@pytest.mark.parametrize(
    'message',
    (1, 5, 10)
)
def _test_language_test_execution(user_session_handler, user_session, message):
    user_session = _update_step(user_session_handler, user_session, 2)
    answer = user_session_handler.handle_session(user_session, message)
    number_answers = user_session.language_test.number_answers
    assert isinstance(answer, Answer)
    assert answer.text == f'Ответ д. б. в диапазоне от 1 до {number_answers}'
    assert isinstance(answer.keyboard, ReplyKeyboardMarkup)


def test_language_test_execution_r(user_session_handler, user_session):
    # all answers right
    user_session = _update_step(user_session_handler, user_session, 2)
    number_questions = len(user_session.language_test.questions)
    for number in range(number_questions):
        current_question_id = user_session.language_test.current_question
        question = user_session.language_test.questions[current_question_id]
        message = question.right_answer + 1
        answer = user_session_handler.handle_session(user_session, message)
        if number < number_questions - 1:
            assert isinstance(answer, Answer)
            assert isinstance(answer.keyboard, ReplyKeyboardMarkup)
        else:
            assert isinstance(answer, tuple)
            assert isinstance(answer[0], Answer)
            assert isinstance(answer[1], CloseSession)

            final_message = (f'Вы ответили верно на {number_questions} вопроса '
                             f'из {number_questions}. Ваш результат: 100 %')
            assert answer[0].text == final_message


def test_language_test_execution_w(user_session_handler, user_session):
    # all answers wrong
    user_session = _update_step(user_session_handler, user_session, 2)
    number_questions = len(user_session.language_test.questions)
    wrong_answers = [
        (index + 1, question)
        for index, question in enumerate(user_session.language_test.questions)
    ]
    for number in range(number_questions):
        current_question_id = user_session.language_test.current_question
        question = user_session.language_test.questions[current_question_id]
        message = 1 if question.right_answer + 1 != 1 else 2
        answer = user_session_handler.handle_session(user_session, message)
        if number < number_questions - 1:
            assert isinstance(answer, Answer)
            assert isinstance(answer.keyboard, ReplyKeyboardMarkup)
        else:
            assert isinstance(answer, tuple)
            assert isinstance(answer[0], Answer)
            assert isinstance(answer[1], CloseSession)

            fmt_wrong_answers = _get_fmt_wrong_answers(wrong_answers)
            final_message = (f'Вы ответили верно на 0 вопросов из '
                             f'{number_questions}. Ваш результат: 0 %\n'
                             f'{fmt_wrong_answers}')
            assert answer[0].text == final_message
