import asyncio
import logging
import os.path
from typing import NoReturn, Sequence, Tuple, Union

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.types import ContentType
from aiogram.utils import executor

from core.config import BASE_DIR, TOKEN
from core.db import close_connection, create_connection
from core.dispatcher import SessionsDispatcher
from core.init_db import check_db_exists
from core.handlers import (
    language_test_creator_session_handler,
    user_session_handler
)
from core.types import Answer, CloseSession


logging.basicConfig(
    filename=os.path.join(BASE_DIR, 'log.log'),
    filemode='a',
    level=logging.INFO,
    format='[%(levelname)-8s] [%(filename)-18s] [%(asctime)s] [%(message)s]',
    datefmt='%Y-%m-%d %H:%M:%S'
)


dp = SessionsDispatcher()
dp.register_handlers(
    language_test_creator_session_handler,
    user_session_handler,
)
loop = asyncio.get_event_loop()
loop.create_task(dp.close_old_sessions())
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, storage=MemoryStorage(), loop=loop)


@dispatcher.message_handler()
async def process_message(message: types.Message) -> None:
    answers = dp.handle_text_message(
        message.from_user.id, message.text, message.date
    )
    await _process_answers(message.from_user.id, answers)


@dispatcher.message_handler(content_types=ContentType.DOCUMENT)
async def process_document(message: types.Message) -> None:
    document = await bot.download_file_by_id(message.document.file_id)
    answers = dp.handle_document(message.from_user.id, document)
    await _process_answers(message.from_user.id, answers)


async def _process_answers(user_id: int, answers: Union[Answer, Tuple]) -> None:
    if isinstance(answers, Answer):
        await _send_answer(user_id, answers)
    elif isinstance(answers, Sequence):
        for answer in answers:
            if isinstance(answer, Answer):
                await _send_answer(user_id, answer)
            elif isinstance(answer, CloseSession):
                dp.close_session(user_id)


async def _send_answer(user_id: int, answer: Answer) -> None:
    await bot.send_message(
        chat_id=user_id,
        text=answer.text,
        reply_markup=answer.keyboard
    )


async def on_shutdown(_):
    close_connection()


def main() -> NoReturn:
    create_connection('language_bot_db.db')
    check_db_exists()
    executor.start_polling(
        dispatcher, skip_updates=True, timeout=60, on_shutdown=on_shutdown
    )


if __name__ == '__main__':
    main()
