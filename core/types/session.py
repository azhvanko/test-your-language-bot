from dataclasses import dataclass
from datetime import datetime


@dataclass
class Session:
    handler_alias: str
    user_id: int
    created: datetime
    current_step: int = 0


@dataclass
class UserSession(Session):
    pass


@dataclass
class TestCreatorSession(Session):
    pass


class CloseSession:
    pass
