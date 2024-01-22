import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv

from bot_templates import Buttons, Messages
from logger import Logger

load_dotenv("bot.env")
token = os.getenv("BOT_TOKEN")

logger = Logger(__name__)
bot = Bot(token=token)
dp = Dispatcher(bot=bot)


@dp.message_handler(commands=["start"])
async def start(message: types.Message) -> None:
    await log_event(message)

    reply_markup = await keyboard(Buttons.MAIN_MENU.value)

    await bot.send_message(message.from_user.id, Messages.START.value, reply_markup=reply_markup)


@dp.message_handler(Text(equals=Buttons.GITHUB.value))
async def button_github(message: types.Message) -> None:
    await log_event(message)

    reply_markup = await keyboard(Buttons.MAIN_MENU.value)

    await bot.send_message(
        message.from_user.id,
        Messages.GITHUB.value,
        reply_markup=reply_markup,
        disable_web_page_preview=True,
        parse_mode=types.ParseMode.MARKDOWN,
    )


@dp.message_handler(Text(equals=Buttons.COFFEE.value))
async def button_coffee(message: types.Message) -> None:
    await log_event(message)

    reply_markup = await keyboard(Buttons.MAIN_MENU.value)

    await bot.send_message(
        message.from_user.id,
        Messages.COFFEE.value,
        reply_markup=reply_markup,
        disable_web_page_preview=True,
        parse_mode=types.ParseMode.MARKDOWN,
    )


async def keyboard(
    buttons: list[str] | dict[str, str]
) -> ReplyKeyboardMarkup | InlineKeyboardMarkup:
    if isinstance(buttons, list):
        keyboard = ReplyKeyboardMarkup(
            resize_keyboard=True,
        )
        for button in buttons:
            keyboard.add(KeyboardButton(button))

    elif isinstance(buttons, dict):
        keyboard = InlineKeyboardMarkup(
            row_width=2,
        )
        for callback_data, text in buttons.items():
            keyboard.add(InlineKeyboardButton(callback_data=callback_data, text=text))

    return keyboard


async def log_event(data: types.Message | types.CallbackQuery) -> None:
    try:
        logger.debug(
            f"Message from {data.from_user.username} with telegram ID {data.from_user.id}: {data.text}"
        )
    except AttributeError:
        logger.debug(
            f"Callback from {data.from_user.username} with telegram ID {data.from_user.id}: {data.data}"
        )


if __name__ == "__main__":
    executor.start_polling(dp)
