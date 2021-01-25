import asyncio
import logging
import os.path
from typing import NoReturn, Tuple, Union

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.types import ContentType
from aiogram.utils import executor

from core.config import BASE_DIR, TOKEN
from core.dispatcher import SessionsDispatcher
from core.types import Answer


logging.basicConfig(
    filename=os.path.join(BASE_DIR, 'log.log'),
    filemode='a',
    level=logging.INFO,
    format='[%(levelname)-8s] [%(filename)-18s] [%(asctime)s] [%(message)s]',
    datefmt='%Y-%m-%d %H:%M:%S'
)


dp = SessionsDispatcher()
loop = asyncio.get_event_loop()
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
    pass


async def _send_answer() -> None:
    pass


def main() -> NoReturn:
    executor.start_polling(dispatcher, skip_updates=True, timeout=60)


if __name__ == '__main__':
    main()
