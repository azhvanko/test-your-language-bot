from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .language_test import LanguageTest


@dataclass
class Session:
    handler_alias: str
    user_id: int
    created: datetime
    current_step: int = 0


@dataclass
class UserSession(Session):
    language_id: Optional[int] = None
    test_type_id: Optional[int] = None
    language_test: Optional[LanguageTest] = None


@dataclass
class LanguageTestCreatorSession(Session):
    command: Optional[str] = None


class CloseSession:
    pass
