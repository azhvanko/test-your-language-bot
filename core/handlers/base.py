import functools
import io
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable, Dict, Optional, Tuple, Union

from core.types import Answer, CloseSession, Session


class SessionHandler(ABC):

    def __init__(self, alias: str, steps: Tuple[str, ...]):
        self._alias = alias
        self._steps = steps
        self._functions_map: Dict[str, Callable] = {}

    @abstractmethod
    def get_data_class(self, user_id: int, date: datetime) -> Session:
        """Returns Session depending on the type of session handler."""
        pass

    @property
    def last_step(self) -> int:
        return len(self._steps) - 1

    @property
    def alias(self) -> str:
        return self._alias

    @alias.setter
    def alias(self, value: str):
        self._alias = value

    def handle_session(
            self,
            session: Session,
            message: Optional[Union[str, io.BytesIO]] = None
    ) -> Union[Answer, Tuple[Answer, Answer], Tuple[Answer, CloseSession]]:
        func = self._get_step_handler(session.current_step)
        return func(session, message)

    def _get_step_handler(self, step: int) -> Callable:
        step_alias = self._steps[step]
        return self._functions_map[step_alias]

    def update_current_step(self, session: Session) -> None:
        if session.current_step < self.last_step:
            session.current_step += 1

    def register_function(self, alias: str) -> Callable:
        """Decorator for registering handler functions."""
        def function_decorator(func):
            if alias not in self._steps:
                raise KeyError(
                    f'Псевдоним {alias} функции {func.__name__} не '
                    f'был добавлен в список steps'
                )
            func.alias = alias
            self._functions_map[alias] = func

            @functools.wraps(func)
            def inner(self, *args, **kwargs):
                return func(self, *args, **kwargs)

            return inner

        return function_decorator
