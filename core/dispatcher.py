import io
import re
from datetime import datetime
from typing import Dict, Optional, Tuple

from .config import COMMANDS
from .types import Answer


class SessionsDispatcher:
    """User sessions dispatcher."""

    def __init__(self):
        self._handlers = {}
        self._sessions = {}
        self._default_answers: Dict[str, str] = {
            'unsupported_command': 'Данная команда не поддерживается',
        }

    def handle_text_message(self, user_id: int, text: str, date: datetime):
        if self._is_bot_command(text):
            return self._handle_command(user_id, text, date)
        else:
            return self._handle_text(user_id, text)

    def handle_document(self, user_id: int, document: io.BytesIO):
        pass

    def _handle_command(self, user_id: int, text: str, date: datetime):
        command, deep_link = self._get_bot_command(text)

        if command in COMMANDS['start_commands']:
            return self._handle_start_commands(user_id, command, date, deep_link)

        if command in COMMANDS['user_commands']:
            return self._handle_user_commands(user_id, date)

        if command in COMMANDS['test_creator_commands']:
            return self._handle_test_creator_commands(user_id, command, date)

        if command in COMMANDS['information_commands']:
            return self._handle_information_commands(command)

        if command in COMMANDS['admin_commands']:
            return self._handle_admin_commands(user_id, command)

        return Answer(text=self._get_default_answer('unsupported_command'))

    def _handle_text(self, user_id: int, text: str):
        pass

    def _handle_start_commands(
            self, user_id: int, command: str, date: datetime, deep_link: Optional[str]
    ) -> Answer:
        pass

    def _handle_user_commands(self, user_id: int, date: datetime):
        pass

    def _handle_test_creator_commands(self, user_id: int, command: str, date: datetime):
        pass

    def _handle_information_commands(self, command: str) -> Answer:
        pass

    def _handle_admin_commands(self, user_id: int, command: str) -> Answer:
        pass

    def _get_default_answer(self, key: str) -> str:
        return self._default_answers[key]

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
