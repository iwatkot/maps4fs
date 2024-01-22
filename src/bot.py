import asyncio
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from dotenv import load_dotenv

from bot_templates import Buttons, Messages
from logger import Logger

load_dotenv("bot.env")
token = os.getenv("BOT_TOKEN")

logger = Logger("bot")
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: types.Message) -> None:
    await log_event(message)

    kb = await keyboard(Buttons.MAIN_MENU.value)

    await message.answer(Messages.START.value, reply_markup=kb.as_markup())


@dp.message(F.text == Buttons.GITHUB.value)
async def button_github(message: types.Message) -> None:
    await log_event(message)

    kb = await keyboard(Buttons.MAIN_MENU.value)

    await message.answer(
        Messages.GITHUB.value,
        reply_markup=kb.as_markup(),
        disable_web_page_preview=True,
    )


@dp.message(F.text == Buttons.COFFEE.value)
async def button_coffee(message: types.Message) -> None:
    await log_event(message)

    kb = await keyboard(Buttons.MAIN_MENU.value)

    await message.answer(
        Messages.COFFEE.value,
        reply_markup=kb.as_markup(),
        disable_web_page_preview=True,
    )


async def keyboard(
    buttons: list[str] | dict[str, str]
) -> ReplyKeyboardBuilder | InlineKeyboardBuilder:
    if isinstance(buttons, list):
        builder = ReplyKeyboardBuilder()
        for button in buttons:
            builder.button(text=button)
        builder.adjust(1, 2)

    # elif isinstance(buttons, dict):
    #     keyboard = InlineKeyboardMarkup(
    #         row_width=2,
    #     )
    #     for callback_data, text in buttons.items():
    #         keyboard.add(InlineKeyboardButton(callback_data=callback_data, text=text))

    return builder


async def log_event(data: types.Message | types.CallbackQuery) -> None:
    try:
        logger.debug(
            f"Message from {data.from_user.username} with telegram ID {data.from_user.id}: {data.text}"
        )
    except AttributeError:
        logger.debug(
            f"Callback from {data.from_user.username} with telegram ID {data.from_user.id}: {data.data}"
        )


async def main() -> None:
    bot = Bot(token, parse_mode=ParseMode.MARKDOWN_V2)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
