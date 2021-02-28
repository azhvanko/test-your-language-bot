from typing import List, Union

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_keyboard(
        buttons: List[Union[int, str]], row_width: int = 3
) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True,
        row_width=row_width
    ).add(*[KeyboardButton(button) for button in buttons])
