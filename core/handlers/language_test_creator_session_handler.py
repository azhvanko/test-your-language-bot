from datetime import datetime
from typing import Tuple

from core.handlers import SessionHandler
from core.types import TestCreatorSession


class LanguageTestCreatorSessionHandler(SessionHandler):

    def __init__(self, alias: str, steps: Tuple[str, ...]):
        super().__init__(alias, steps)

    def get_data_class(self, user_id: int, date: datetime) -> TestCreatorSession:
        return TestCreatorSession(handler_alias=self.alias, user_id=user_id, created=date)


language_test_creator_session_handler = LanguageTestCreatorSessionHandler(
    'language_test_creator_session_handler',
    (
        'get_start_message',
        'handle_language_test',
    )
)

_ltcsh = language_test_creator_session_handler
