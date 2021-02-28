import asyncio
import io
import re
from datetime import datetime
from typing import Dict, Optional, Tuple, Union

from core.config import COMMANDS
from core.db import (
    add_new_user,
    create_deep_link,
    get_formatted_languages_list,
    get_formatted_test_types_list,
    get_user_role,
    is_new_user,
    update_user_role
)
from core.handlers import SessionHandler
from core.types import Answer, CloseSession, Session


class UnclosedSessionError(Exception):
    pass


class SessionsDispatcher:
    """User sessions dispatcher."""

    def __init__(self):
        self._handlers = {}
        self._sessions = {}
        self._default_answers: Dict[str, str] = {
            'invalid_message': (
                'Для начала работы с ботом используйте одну из доступных команд'
            ),
            'unsupported_command': 'Данная команда не поддерживается',
        }

    def handle_text_message(
            self, user_id: int, text: str, date: datetime
    ) -> Union[Answer, Tuple[Answer, Answer], Tuple[Answer, CloseSession]]:
        if self._is_bot_command(text):
            return self._handle_command(user_id, text, date)
        else:
            return self._handle_text(user_id, text)

    def handle_document(
            self, user_id: int, document: io.BytesIO
    ) -> Union[Answer, Tuple[Answer, CloseSession]]:
        if user_id in self._sessions:
            handler_alias = self._sessions[user_id].handler_alias
            handler = self._get_handler(handler_alias)
            return handler.handle_session(self._sessions[user_id], message=document)
        return Answer(text=self._get_default_answer('invalid_message'))

    def _handle_command(
            self, user_id: int, text: str, date: datetime
    ) -> Union[Answer, Tuple[Answer, Answer]]:
        command, deep_link = self._get_bot_command(text)

        if command in COMMANDS['start_commands']:
            return self._handle_start_commands(user_id, command, date, deep_link)

        if command in COMMANDS['user_commands']:
            return self._handle_user_commands(user_id, date)

        if command in COMMANDS['test_creator_commands']:
            return self._handle_language_test_creator_commands(user_id, command, date)

        if command in COMMANDS['information_commands']:
            return self._handle_information_commands(user_id, command)

        if command in COMMANDS['admin_commands']:
            return self._handle_admin_commands(user_id, command)

        return Answer(text=self._get_default_answer('unsupported_command'))

    def _handle_text(
            self, user_id: int, text: str
    ) -> Union[Answer, Tuple[Answer, Answer], Tuple[Answer, CloseSession]]:
        if user_id in self._sessions:
            handler_alias = self._sessions[user_id].handler_alias
            handler = self._get_handler(handler_alias)
            return handler.handle_session(self._sessions[user_id], message=text)
        return Answer(text=self._get_default_answer('invalid_message'))

    def _handle_start_commands(
            self, user_id: int, command: str, date: datetime, deep_link: Optional[str]
    ) -> Answer:
        if command == 'start':
            if is_new_user(user_id):
                add_new_user(user_id, date, deep_link)
            else:
                if deep_link is not None:
                    update_user_role(user_id, date, deep_link)
        self.close_session(user_id)
        role = get_user_role(user_id)
        return self._get_start_message(command, role)

    def _handle_user_commands(
            self, user_id: int, date: datetime
    ) -> Answer:
        handler_alias = 'user_session_handler'
        handler = self._get_handler(handler_alias)
        try:
            session = self._create_session(user_id, date, handler)
        except UnclosedSessionError as e:
            return Answer(text=str(e))
        return handler.handle_session(session)

    def _handle_language_test_creator_commands(
            self, user_id: int, command: str, date: datetime
    ) -> Union[Answer, Tuple[Answer, CloseSession]]:
        handler_alias = 'language_test_creator_session_handler'
        user_role = get_user_role(user_id)
        if user_role == 'user':
            return Answer(text=self._get_default_answer('unsupported_command'))
        handler = self._get_handler(handler_alias)
        handler.alias = handler_alias
        try:
            session = self._create_session(user_id, date, handler)
        except UnclosedSessionError as e:
            return Answer(text=str(e))
        return handler.handle_session(session, command)

    def _handle_information_commands(self, user_id: int, command: str) -> Answer:
        if get_user_role(user_id) == 'user':
            return Answer(text=self._get_default_answer('unsupported_command'))
        if command == 'languages_list':
            return Answer(text=get_formatted_languages_list())
        if command == 'test_types_list':
            return Answer(text=get_formatted_test_types_list())

    def _handle_admin_commands(self, user_id: int, command: str) -> Answer:
        user_role = get_user_role(user_id)
        if user_role != 'admin':
            return Answer(text=self._get_default_answer('unsupported_command'))
        if command == 'create_deep_link':
            deep_link = create_deep_link(user_id)
            return Answer(text=f'Ссылка успешно создана.\n{deep_link}')

    def _get_default_answer(self, key: str) -> str:
        return self._default_answers[key]

    @staticmethod
    def _get_start_message(command: str, role: str) -> Answer:
        start_message = (
            'Привет!\n'
            'С помощью этого бота вы сможете проверить ваши знания грамматики '
            'и лексики иностранного языка.\n\n'
        )
        user_commands = 'Для того, чтобы начать тест, введите /begin_test.\n'
        test_creator_commands = (
            'Для того, чтобы получить список языков, введите /languages_list.\n'
            'Для того, чтобы получить список доступных типов тестов, введите '
            '/test_types_list.\nДля того, чтобы добавить вопросы, введите '
            '/add_questions, чтобы обновить  - /update_questions, чтобы удалить '
            '- /delete_questions.\n'
        )
        admin_commands = 'Для того, чтобы создать deeplink, введите /create_deep_link.'
        if role == 'user':
            text = user_commands
        elif role == 'test_creator':
            text = f'{user_commands}{test_creator_commands}'
        else:
            text = f'{user_commands}{test_creator_commands}{admin_commands}'
        if command == 'start':
            text = f'{start_message}{text}'
        return Answer(text=text)

    def _create_session(
            self, user_id: int, date: datetime, handler: SessionHandler
    ) -> Session:
        if user_id in self._sessions:
            raise UnclosedSessionError(
                'Вы должны завершить предыдущую сессию.\n Введите команду '
                '/reset, если хотите начать сначала.')
        self._sessions[user_id] = handler.get_data_class(user_id, date)
        return self._sessions[user_id]

    def close_session(self, user_id: int) -> None:
        self._sessions.pop(user_id, None)

    async def close_old_sessions(self) -> None:
        time_limit = 1800  # 30 min
        while True:
            await asyncio.sleep(time_limit / 3)
            current_time = self._get_now_datetime()

            close_list = set()
            for chat_id, session in self._sessions.items():
                if (current_time - session.created).total_seconds() > time_limit:
                    close_list.add(chat_id)

            for chat_id in close_list:
                self.close_session(chat_id)

    def register_handlers(self, *args) -> None:
        for handler in args:
            if not isinstance(handler, SessionHandler):
                raise KeyError('Все аргументы д. б. подклассами класса '
                               '"SessionHandler"')
            self._handlers[handler.alias] = handler

    def _get_handler(self, handler_alias: str) -> SessionHandler:
        return self._handlers[handler_alias]

    @staticmethod
    def _is_bot_command(text: str) -> bool:
        """Returns True if the text is a valid telegram bot command."""
        pattern = r'^/[a-z0-9_]+'
        match = re.search(pattern, text, flags=re.MULTILINE)
        return bool(match)

    @staticmethod
    def _get_bot_command(text: str) -> Tuple[str, Optional[str]]:
        """Returns bot command and optional deep link."""
        command_pattern = r'^/[a-z0-9_]+'
        match = re.search(command_pattern, text, flags=re.MULTILINE)
        command = match.group()[1:]
        deep_link_pattern = r'\s[a-z0-9-]+$'
        match = re.search(deep_link_pattern, text, flags=re.MULTILINE)
        if match is not None and len(match.group()[1:]) == 36:
            deep_link = match.group()[1:]
        else:
            deep_link = None
        return (command, deep_link)

    @staticmethod
    def _get_now_datetime() -> datetime:
        return datetime.now()
