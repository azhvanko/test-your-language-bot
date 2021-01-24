import asyncio
import logging
import os.path
from typing import NoReturn

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.types import ContentType
from aiogram.utils import executor

from core.config import BASE_DIR, TOKEN


logging.basicConfig(
    filename=os.path.join(BASE_DIR, 'log.log'),
    filemode='a',
    level=logging.INFO,
    format='[%(levelname)-8s] [%(filename)-18s] [%(asctime)s] [%(message)s]',
    datefmt='%Y-%m-%d %H:%M:%S'
)


loop = asyncio.get_event_loop()
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, storage=MemoryStorage(), loop=loop)


@dispatcher.message_handler()
async def process_message(message: types.Message) -> None:
    pass


@dispatcher.message_handler(content_types=ContentType.DOCUMENT)
async def process_document(message: types.Message) -> None:
    pass


async def _process_answers() -> None:
    pass


async def _send_answer() -> None:
    pass


def main() -> NoReturn:
    executor.start_polling(dispatcher, skip_updates=True, timeout=60)


if __name__ == '__main__':
    main()
