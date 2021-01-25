from dataclasses import dataclass
from typing import Union

from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove


@dataclass(frozen=True)
class Answer:
    """Structure answer to the user message."""
    text: str
    keyboard: Union[ReplyKeyboardMarkup,
                    ReplyKeyboardRemove] = ReplyKeyboardRemove()
