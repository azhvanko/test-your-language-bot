import io
import json
import logging
from typing import Dict, KeysView, List, Type, Union

from core.db import (
    get_all_languages,
    get_all_questions,
    get_all_test_types,
    normalize_question
)
from core.exceptions import *


language_test_keys = {
    'language': str,
    'test_type': (int, str),
    'questions': list,
}
question_keys = {
    'question': str,
    'answers': list,
    'right_answer': str,
}


def check_language_test(file: io.BytesIO, check_duplicates: bool = True) -> Dict:
    try:
        data = json.loads(file.read().decode(encoding='utf-8'))
        _check_language_test_content(data, check_duplicates)
    except LanguageTestError as e:
        raise e
    except Exception:
        raise FileError(
            'Не удалось прочитать JSON.\n'
            'Пожалуйста, проверьте корректность вашего документа, а также '
            'убедитесь в том, что он сохранён в кодировке UTF-8.'
        )
    else:
        return data


def _check_language_test_content(
        data: Dict[str, Union[str, int, List]],
        check_duplicates: bool
) -> None:
    try:
        _check_keys(data, language_test_keys.keys())
        _check_keys_type(data, language_test_keys)
        _check_language(data['language'])
        _check_test_type(data['test_type'])
        _check_questions(data['questions'], check_duplicates)
    except LanguageTestError as e:
        raise e
    except Exception as e:
        logging.exception(msg=e)
        raise LanguageTestError(
            'Не удалось проверить ваше тест.\n Пожалуйста, проверьте '
            'корректность вашего теста и пришлите тест ещё раз.'
        )
    else:
        pass


def _check_keys(
        data: Dict[str, Union[str, int, List]],
        keys: KeysView[str]
) -> None:
    for key in keys:
        if data.get(key, None) is None:
            raise KeyMissingError(f'В вашем JSON отсутствует ключ - {key}')


def _check_language(language: str) -> None:
    all_languages = [language[0] for language in get_all_languages('code')]
    if language.strip().upper() in all_languages:
        return
    raise LanguageTypeError(
        'Вы прислали неподдерживаемый язык.\n Для получения списка актуальных '
        'языков пришлите команду /languages_list'
    )


def _check_test_type(test_type: Union[int, str]) -> None:
    try:
        test_types = get_all_test_types(ids=True)
        flag = int(test_type) in test_types
    except ValueError:
        raise LanguageTestTypeError(
            'Вы прислали некорректное число в поле "test_type"'
        )
    else:
        if not flag:
            raise LanguageTestTypeError(
                'Вы прислали неподдерживаемый тип теста.\n Для получения '
                'актуального списка типов тестов пришлите команду /test_types_list'
            )


def _check_questions(
        questions: List[Dict[str, Union[str, List]]],
        check_duplicates: bool
) -> None:
    if not questions:
        raise EmptyQuestionsListError('Вы прислали пустой список вопросов.')
    for question in questions:
        _check_keys(question, question_keys.keys())
        _check_keys_type(question, question_keys)
        _check_number_answers(question)
        _check_right_answer(question)
        if check_duplicates:
            _check_duplicate_questions(questions)


def _check_keys_type(
        data: Dict[str, Union[str, List]],
        keys: Dict[str, Type[Union[str, List]]],
) -> None:
    for key, value in data.items():
        if not isinstance(value, keys[key]):
            raise KeyTypeError(
                f'Значение в поле "{key}" содержит неверный тип данных.\n'
                f'Корректный тип данных для данного поля - {keys[key]}'
            )


def _check_duplicate_questions(
        questions: List[Dict[str, Union[str, List]]]
) -> None:
    _questions = get_all_questions(0)
    duplicates = []
    for question in questions:
        _normalize_question = normalize_question(question['question'])
        if _normalize_question in _questions:
            duplicates.append(_normalize_question)
    if duplicates:
        fmt_duplicates = '\n'.join(f'{ind}. {val}'
                                   for ind, val in enumerate(duplicates, start=1))
        error_message = (
            f'Обнаружены вопросы, которые ранее уже были загружены.\n'
            f'Список вопросов:\n'
            f'{fmt_duplicates}\n\n'
            f'Пожалуйста, удалите эти вопросы из вашего файла и повторите '
            f'попытку снова.'
        )
        raise DuplicateQuestionError(error_message)


def _check_number_answers(question: Dict[str, Union[str, List]]) -> None:
    if 2 <= len(question['answers']) <= 8:
        return
    msg = (
        'Количество ответов на вопрос должно быть в диапазоне от 2 до 8 '
        '(вопрос - "{question}")'
    )
    raise NumberAnswersError(msg.format(question=question['question']))


def _check_right_answer(question: Dict[str, Union[str, List]]) -> None:
    if question['right_answer'] not in question['answers']:
        raise RightAnswerError(
            f'Указанный вами правильный ответ - "{question["right_answer"]}" '
            f'отсутствует в списке ответов на вопрос - "{question["question"]}"'
        )
