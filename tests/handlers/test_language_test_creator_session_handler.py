import json
import os
from datetime import datetime

import pytest

from core.db import (
    generate_questions_values,
    get_all_questions,
    get_language_id,
    insert_questions,
)
from core.handlers.language_test_creator_session_handler import _get_start_message_text
from core.types import LanguageTestCreatorSession


@pytest.fixture(scope='function')
def language_test_creator_session():
    return LanguageTestCreatorSession(
        'language_test_creator_session_handler',
        1,
        datetime.now()
    )


@pytest.fixture(scope='function')
def language_test_file(tmpdir_factory, random_language_test):
    temp_dir = tmpdir_factory.mktemp('temp')
    temp_path = os.path.join(temp_dir, 'language_test.txt')
    with open(temp_path, mode='w', encoding='utf-8') as file:
        json.dump(random_language_test, file)
    with open(temp_path, mode='rb') as file:
        yield file, random_language_test


def _update_step(
        user_session: LanguageTestCreatorSession,
        command: str
) -> LanguageTestCreatorSession:
    user_session.command = command
    user_session.current_step += 1
    return user_session


@pytest.mark.parametrize(
    'command, result',
    (
        ('add_questions', _get_start_message_text('add_questions')),
        ('delete_questions', _get_start_message_text('delete_questions')),
        ('update_questions', _get_start_message_text('update_questions')),
    )
)
def test_get_start_message(
        language_test_creator_session_handler,
        language_test_creator_session,
        command,
        result
):
    answer = language_test_creator_session_handler.handle_session(
        language_test_creator_session, command
    )
    assert answer.text == result


def test_add_questions(
        language_test_file,
        language_test_creator_session_handler,
        language_test_creator_session
):
    file, language_test = language_test_file
    _session = _update_step(language_test_creator_session, 'add_questions')
    _ = language_test_creator_session_handler.handle_session(_session, file)
    question = language_test['questions'][0]['question']
    assert question in get_all_questions(1)


def test_delete_questions(
        language_test_file,
        language_test_creator_session_handler,
        language_test_creator_session
):
    file, language_test = language_test_file
    language_id = get_language_id(language_test['language'], 'code')
    values = generate_questions_values(
        1, language_id, language_test['language'], language_test['questions']
    )
    insert_questions(values)
    question = language_test['questions'][0]['question']
    _session = _update_step(language_test_creator_session, 'delete_questions')
    _ = language_test_creator_session_handler.handle_session(_session, question)
    assert question not in get_all_questions(1)
