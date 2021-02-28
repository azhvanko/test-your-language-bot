import io
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Union

from core.check_language_test import check_language_test
from core.db import (
    delete_questions,
    generate_questions_values,
    get_all_questions,
    get_language_id,
    insert_questions,
    normalize_question
)
from core.exceptions import LanguageTestError
from core.handlers import SessionHandler
from core.types import Answer, CloseSession, LanguageTestCreatorSession


class LanguageTestCreatorSessionHandler(SessionHandler):

    def __init__(self, alias: str, steps: Tuple[str, ...]):
        super().__init__(alias, steps)

    def get_data_class(
            self, user_id: int, date: datetime
    ) -> LanguageTestCreatorSession:
        return LanguageTestCreatorSession(
            handler_alias=self.alias, user_id=user_id, created=date
        )


language_test_creator_session_handler = LanguageTestCreatorSessionHandler(
    'language_test_creator_session_handler',
    (
        'get_start_message',
        'handle_language_test',
    )
)

_ltcsh = language_test_creator_session_handler


@_ltcsh.register_function(alias='get_start_message')
def _get_start_message(
        session: LanguageTestCreatorSession,
        message: str
) -> Answer:
    session.command = message
    text = _get_start_message_text(message)
    _ltcsh.update_current_step(session)
    return Answer(text=text)


@_ltcsh.register_function(alias='handle_language_test')
def _handle_language_test(
        session: LanguageTestCreatorSession,
        message: [str, io.BytesIO]
) -> Tuple[Answer, CloseSession]:
    answer_text = _handle_test_creator_message(
        session.command, session.user_id, message
    )
    return (Answer(text=answer_text), CloseSession())


def _get_start_message_text(command: str) -> str:
    if command == 'add_questions':
        return 'OK! Пришлите мне ваши вопросы в формате JSON.'
    elif command == 'delete_questions':
        return ('OK! Пришлите мне ваш вопрос строкой или если вопросов '
                'несколько - текстовый файл (все вопросы в файле должны идти '
                'с новой строки, т. е. 1 строка - 1 вопрос.')
    elif command == 'update_questions':
        return 'OK! Пришлите мне ваши вопросы в формате JSON.'
    else:
        return 'Что-то пошло не так. Пожалуйста, пришлите другую команду.'


def _handle_test_creator_message(
        command: str,
        user_id: int,
        message: Union[str, io.BytesIO]
) -> str:
    if command == 'add_questions':
        return _handle_add_questions_command(user_id, message)
    elif command == 'delete_questions':
        return _handle_delete_questions_command(user_id, message)
    elif command == 'update_questions':
        return _handle_update_questions_command(user_id, message)


def _handle_add_questions_command(user_id: int, file: io.BytesIO) -> str:
    try:
        data = check_language_test(file)
    except Exception as e:
        return str(e)
    else:
        answer_text = _add_questions(user_id, data)
        return answer_text


def _handle_delete_questions_command(
        user_id: int,
        data: [str, io.BytesIO]
) -> str:
    try:
        if isinstance(data, str):
            answer_text = _delete_question(user_id, data)
        elif isinstance(data, io.BytesIO):
            answer_text = _delete_questions(user_id, data)
        else:
            raise LanguageTestError(
                'Один вопрос м. б. в виде строки, несколько вопросов д. б. в '
                'виде текстового файла, в которым каждый вопрос для удаления '
                'идёт с новой строки'
            )
    except LanguageTestError as e:
        return str(e)
    else:
        return answer_text


def _handle_update_questions_command(
        user_id: int,
        data: [str, io.BytesIO]
) -> str:
    try:
        if isinstance(data, io.BytesIO):
            answer_text = _update_questions(user_id, data)
        else:
            raise LanguageTestError(
                'Список вопросов д. б. в виде текстового файла'
            )
    except LanguageTestError as e:
        return str(e)
    else:
        return answer_text


def _delete_question(user_id: int, question: str) -> str:
    user_questions = get_all_questions(user_id)
    question = normalize_question(question)
    if question in user_questions:
        delete_questions([user_questions[question], ])
        return 'Вопрос успешно удалён!'
    return ('Не удалось найти присланный вами вопрос.\n'
            'Не было удалено ни одного вопроса.')


def _delete_questions(user_id: int, file: io.BytesIO) -> str:
    try:
        del_questions = _get_questions(file)
    except Exception as e:
        return str(e)
    else:
        if not del_questions:
            return 'Присланный вами список вопросов пуст'
        questions = get_all_questions(user_id)
        question_ids, missed_questions = [], []
        for question in del_questions:
            if question in questions:
                question_ids.append(questions[question])
            else:
                missed_questions.append(question)
        if question_ids:
            delete_questions(question_ids)
        if missed_questions:
            fmt_missed_questions = '\n'.join(
                f'{ind}. {val}'
                for ind, val in enumerate(missed_questions, start=1)
            )
            return (f'Были удалены не все вопросы из вашего списка.\n'
                    f'Список вопросов, которые не были ранее загружены:\n'
                    f'{fmt_missed_questions}')
        else:
            return 'Все вопросы были успешно удалены!'


def _update_questions(user_id: int, file: io.BytesIO) -> str:
    try:
        data = check_language_test(file, False)
    except Exception as e:
        return str(e)
    else:
        questions = get_all_questions(user_id)
        question_ids, missed_questions, upd_questions = [], [], []
        for question in data['questions']:
            _question = normalize_question(question['question'])
            if _question in questions:
                question_ids.append(questions[_question])
                upd_questions.append(question)
            else:
                missed_questions.append(_question)
        if question_ids:
            delete_questions(question_ids)
            language_id = get_language_id(data['language'].upper(), 'code')
            values = generate_questions_values(
                user_id, language_id, int(data['test_type']), upd_questions
            )
            insert_questions(values)
        if missed_questions:
            fmt_missed_questions = '\n'.join(
                f'{ind}. {val}'
                for ind, val in enumerate(missed_questions, start=1)
            )
            return (f'Были обновлены не все вопросы из вашего списка.\n'
                    f'Список вопросов, которые не были ранее загружены:\n'
                    f'{fmt_missed_questions}')
        else:
            return 'Все вопросы были успешно обновлены!'


def _add_questions(user_id: int, data: Dict) -> str:
    language_id = get_language_id(data['language'].upper(), 'code')
    values = generate_questions_values(
        user_id, language_id, int(data['test_type']), data['questions']
    )
    insert_questions(values)
    return 'Ваши вопросы были успешно добавлены!'


def _get_questions(file: io.BytesIO) -> List[str]:
    try:
        questions = [
            normalize_question(question.decode(encoding='utf-8'))
            for question in file.readlines()
        ]
    except Exception as e:
        logging.exception(msg=e)
        raise UnicodeError('Не удалось прочитать ваш файл.\n'
                           'Пожалуйста, проверьте корректность вашего '
                           'документа, а также убедитесь в том, что он '
                           'сохранён в кодировке UTF-8.')
    else:
        return questions
