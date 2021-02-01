from datetime import datetime
from random import shuffle
from typing import List, Optional, Tuple, Union

from aiogram.types import ReplyKeyboardMarkup

from core.db import (
    generate_answer_values,
    get_current_languages,
    get_language_id,
    get_language_test,
    get_test_type_id,
    get_test_types,
    insert_user_answers,
    is_supported_language,
    is_supported_test_type
)
from core.handlers import SessionHandler
from core.keyboard import get_keyboard
from core.types import (
    Answer,
    CloseSession,
    LanguageTest,
    Question,
    UserSession
)


class UserSessionHandler(SessionHandler):

    def __init__(self, alias: str, steps: Tuple[str, ...]):
        super().__init__(alias, steps)

    def get_data_class(self, user_id: int, date: datetime) -> UserSession:
        return UserSession(handler_alias=self.alias, user_id=user_id, created=date)


user_session_handler = UserSessionHandler(
    'user_session_handler',
    (
        'select_language',
        'select_test_type',
        'generate_language_test',
        'language_test_execution',
    )
)

_ush = user_session_handler


@_ush.register_function(alias='select_language')
def _select_language(session: UserSession, message: Optional[str]) -> Answer:
    if message is None or not is_supported_language(message):
        current_languages = get_current_languages()
        keyboard = get_keyboard(current_languages, row_width=1)
        text = 'Выберите один из доступных языков.'
        if message is not None:
            text = f'Вы прислали неподдерживаемый язык.\n{text}'
        return Answer(text=text, keyboard=keyboard)
    else:
        session.language_id = get_language_id(message.strip())
        _ush.update_current_step(session)
        return _ush.handle_session(session)


@_ush.register_function(alias='select_test_type')
def _select_test_type(session: UserSession, message: Optional[str]) -> Answer:
    if message is None or not is_supported_test_type(message):
        test_types_list = get_test_types(session.language_id)
        keyboard = get_keyboard(test_types_list, row_width=1)
        text = 'Выберите один из доступных типов теста.'
        if message is not None:
            text = f'Вы прислали неверный тип теста\n{text}'
        return Answer(text=text, keyboard=keyboard)
    else:
        session.test_type_id = get_test_type_id(message.strip())
        _ush.update_current_step(session)
        return _ush.handle_session(session)


@_ush.register_function(alias='generate_language_test')
def _generate_language_test(
        session: UserSession, _, number_answers: int = 4, limit: int = 10
) -> Tuple[Answer, Answer]:
    language_test = get_language_test(session.user_id, session.language_id,
                                      session.test_type_id, number_answers, limit)
    fmt_language_test = _get_fmt_language_test(language_test)
    session.language_test = fmt_language_test
    _ush.update_current_step(session)
    return _ush.handle_session(session)


@_ush.register_function(alias='language_test_execution')
def _language_test_execution(
        session: UserSession, message: Optional[str]
) -> Union[Answer, Tuple[Answer, Answer], Tuple[Answer, CloseSession]]:
    if message is None:
        current_question = session.language_test.current_question
        question = session.language_test.get_current_question()
        fmt_question, keyboard = _get_formatted_question(question,
                                                         current_question + 1)
        number_questions = len(session.language_test.questions)
        start_message = (f'Давайте начнём!\n'
                         f'Выберите ваш вариант ответа вместо пропусков.\n'
                         f'Тест состоит из {number_questions} вопросов.')
        return (Answer(text=start_message),
                Answer(text=fmt_question, keyboard=keyboard))

    language_test = session.language_test
    if _is_correct_question_answer(message, language_test.number_answers):
        return _process_user_answer(session.user_id, language_test, int(message))
    else:
        max_number = language_test.number_answers
        keyboard = get_keyboard([i for i in range(1, max_number + 1)], row_width=2)
        return Answer(
            text=f'Ответ д. б. в диапазоне от 1 до {max_number}', keyboard=keyboard
        )


def _get_fmt_language_test(language_test: List[Tuple]) -> LanguageTest:
    questions = []
    for question in language_test:
        answers = list(question[2].split('\n'))
        right_answer = answers[int(question[3])]
        _answers = answers[:]
        shuffle(answers)
        questions.append(
            Question(
                question_id=int(question[0]),
                question=question[1],
                answers=answers,
                old_answers_order=[_answers.index(i) for i in answers],
                right_answer=answers.index(right_answer)
            )
        )
    return LanguageTest(
        questions=questions,
        user_answers=[0 for _ in range(len(questions))],
        number_answers=len(questions[0].answers)
    )


def _process_user_answer(
        user_id: int, language_test: LanguageTest, answer: int
) -> Union[Answer, Tuple[Answer, CloseSession]]:
    language_test.register_answer(answer)
    if len(language_test.questions) - 1 > language_test.current_question:
        language_test.current_question += 1
        fmt_question, keyboard = _get_formatted_question(
            language_test.get_current_question(),
            language_test.current_question + 1
        )
        return Answer(text=fmt_question, keyboard=keyboard)
    else:
        values = generate_answer_values(user_id, language_test)
        insert_user_answers(values)
        return _get_test_result(language_test)


def _get_formatted_question(
        question: Question, number: int
) -> Tuple[str, ReplyKeyboardMarkup]:
    keyboard = get_keyboard(
        [i for i in range(1, len(question.answers) + 1)], row_width=2
    )
    answers = '\n'.join(
        [
            f'{index}. {answer}'
            for index, answer in enumerate(question.answers, start=1)
        ]
    )
    return (f'{number}. {question.question}\n\n{answers}', keyboard)


def _is_correct_question_answer(answer: str, number_answers: int) -> bool:
    try:
        number = int(answer)
    except ValueError:
        return False
    else:
        return 1 <= number <= number_answers


def _get_test_result(language_test: LanguageTest) -> Tuple[Answer, CloseSession]:
    test_score, wrong_answers = _get_test_score(language_test)
    number_questions = len(language_test.questions)
    percent_test_score = test_score / number_questions * 100
    number_right_answers = _get_fmt_count_right_answers(test_score)
    final_message = (f'Вы ответили верно на {number_right_answers} из '
                     f'{number_questions}. Ваш результат: '
                     f'{percent_test_score:.0f} %')
    if percent_test_score < 100:
        fmt_wrong_answers = _get_fmt_wrong_answers(wrong_answers)
        final_message = f'{final_message}\n{fmt_wrong_answers}'
    return (Answer(text=final_message), CloseSession())


def _get_test_score(language_test: LanguageTest) -> Tuple[int, List[Tuple]]:
    test_score = 0
    wrong_answers = []
    for index, question in enumerate(language_test.questions):
        if question.right_answer == language_test.user_answers[index]:
            test_score += 1
        else:
            wrong_answers.append((index + 1, question))
    return (test_score, wrong_answers)


def _get_fmt_count_right_answers(number: int) -> str:
    if number != 11 and number % 10 == 1:
        pattern = 'вопрос'
    elif number in (2, 3, 4) or (number > 20 and number % 10 in (2, 3, 4)):
        pattern = 'вопроса'
    else:
        pattern = 'вопросов'
    return f'{number} {pattern}'


def _get_fmt_wrong_answers(wrong_answers: List[Tuple]) -> str:
    fmt_wrong_answers = []
    for number, question in wrong_answers:
        whole_question = question.get_whole_question()
        fmt_wrong_answers.append(f'{number}. {whole_question}')
    all_fmt_wrong_answers = '\n'.join(fmt_wrong_answers)
    return (f'Список ваших неправильных ответов:\n\n'
            f'{all_fmt_wrong_answers}')
