import os
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv

import generate
from bot_templates import Buttons, Messages
from logger import Logger

logger = Logger(__name__)
working_directory = os.getcwd()
logger.info(f"Working directory: {working_directory}")
env_path = os.path.join(working_directory, "bot.env")
logger.info(f"Environment file: {env_path}")
if not os.path.exists(env_path):
    raise FileNotFoundError(f"Environment file not found: {env_path}")
load_dotenv(env_path)
token = os.getenv("BOT_TOKEN")

logger = Logger(__name__)
bot = Bot(token=token)
dp = Dispatcher(bot=bot)

sessions = {}


class Session:
    """Represents a session of map generation. Stores all the necessary data.

    Args:
        telegram_id (int): Telegram ID of the user.
        coordinates (tuple[float, float]): Coordinates of the center of the map.

    Attributes:
        telegram_id (int): Telegram ID of the user.
        timestamp (int): Timestamp of the session creation.
        name (str): Name of the session.
        coordinates (tuple[float, float]): Coordinates of the center of the map.
        distance (int): Distance from the center of the map to the edge.
        dem_settings (generate.DemSettings): DEM settings.
    """

    def __init__(self, telegram_id: int, coordinates: tuple[float, float]):
        self.telegram_id = telegram_id
        self.timestamp = int(datetime.now().timestamp())
        self.name = f"{self.telegram_id}_{self.timestamp}"
        self.coordinates = coordinates
        self.distance = None
        self.dem_settings = None

    def run(self) -> tuple[str, str]:
        """Runs the session and returns paths to the preview and the archive.

        Returns:
            tuple[str, str]: Paths to the preview and the archive.
        """
        gm = generate.Map(
            working_directory, self.coordinates, self.distance, self.dem_settings, logger, self.name
        )
        preview_path = gm.preview()
        archive_path = gm.pack()
        return preview_path, archive_path


@dp.message_handler(commands=["start"])
async def start(message: types.Message) -> None:
    """Handles the /start command.

    Args:
        message (types.Message): Message, which triggered the handler.
    """
    await log_event(message)

    await bot.send_message(
        message.from_user.id,
        Messages.START.value,
        reply_markup=await keyboard(Buttons.MAIN_MENU.value),
    )


@dp.message_handler(Text(equals=Buttons.GITHUB.value))
async def button_github(message: types.Message) -> None:
    """Handles the GitHub button.

    Args:
        message (types.Message): Message, which triggered the handler.
    """
    await log_event(message)

    await bot.send_message(
        message.from_user.id,
        Messages.GITHUB.value,
        reply_markup=await keyboard(Buttons.MAIN_MENU.value),
        disable_web_page_preview=True,
    )


@dp.message_handler(Text(equals=Buttons.COFFEE.value))
async def button_coffee(message: types.Message) -> None:
    """Handles the Buy me a coffee button.

    Args:
        message (types.Message): Message, which triggered the handler.
    """
    await log_event(message)

    await bot.send_message(
        message.from_user.id,
        Messages.COFFEE.value,
        reply_markup=await keyboard(Buttons.MAIN_MENU.value),
        disable_web_page_preview=True,
    )


@dp.message_handler(Text(equals=Buttons.GENERATE.value))
async def button_generate(message: types.Message) -> None:
    """Handles the Generate button, registers the coordinates handler.

    Args:
        message (types.Message): Message, which triggered the handler.
    """
    await log_event(message)

    dp.register_message_handler(coordinates)

    await bot.send_message(
        message.from_user.id,
        Messages.ENTER_COORDINATES.value,
        reply_markup=await keyboard([Buttons.CANCEL.value]),
        parse_mode=types.ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )


@dp.message_handler(Text(equals=Buttons.CANCEL.value))
async def cancel_button(message: types.Message) -> None:
    """Handles the Cancel button, returns to the main menu.

    Args:
        message (types.Message): Message, which triggered the handler.
    """
    await log_event(message)

    await bot.send_message(
        message.from_user.id,
        Messages.CANCELLED.value,
        reply_markup=await keyboard(Buttons.MAIN_MENU.value),
    )


async def coordinates(message: types.Message) -> None:
    """Handles the coordinates input, can be accessed only as a next step after the Generate button.
    Checks if the coordinates are correct and creates inline buttons for map sizes.

    Args:
        message (types.Message): Message, which triggered the handler.
    """
    await log_event(message)

    if message.text == Buttons.CANCEL.value:
        dp.message_handlers.unregister(coordinates)
        await bot.send_message(
            message.from_user.id,
            Messages.CANCELLED.value,
            reply_markup=await keyboard(Buttons.MAIN_MENU.value),
        )
        return

    try:
        latitude, longitude = message.text.split(",")
        latitude = float(latitude.strip())
        longitude = float(longitude.strip())
    except ValueError:
        await bot.send_message(
            message.from_user.id,
            Messages.WRONG_COORDINATES.value,
            reply_markup=await keyboard([Buttons.CANCEL.value]),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
        return

    telegram_id = message.from_user.id
    sessions[telegram_id] = Session(telegram_id, (latitude, longitude))

    sizes = generate.MAP_SIZES
    indicators = ["🟢", "🟢", "🟡", "🔴"]
    buttons = {}
    for size, indicator in zip(sizes, indicators):
        buttons[f"map_size_{size}"] = f"{indicator} {size} x {size} meters"

    dp.message_handlers.unregister(coordinates)

    await bot.send_message(
        message.from_user.id,
        Messages.SELECT_MAP_SIZE.value,
        reply_markup=await keyboard(buttons),
    )


@dp.callback_query_handler(text_contains="map")
async def map_size_callback(callback_query: types.CallbackQuery) -> None:
    """Handles the callback from the map size inline buttons, creates inline buttons for max heights.

    Args:
        callback_query (types.CallbackQuery): Callback, which triggered the handler.
    """
    await log_event(callback_query)

    map_size = int(callback_query.data.rsplit("_", 1)[-1])
    session = sessions.get(callback_query.from_user.id)
    if not session:
        return
    session.distance = int(map_size / 2)

    heights = generate.MAX_HEIGHTS
    buttons = {}
    for height, description in heights.items():
        buttons[f"max_height_{height}"] = description

    await bot.send_message(
        callback_query.from_user.id,
        Messages.SELECT_MAX_HEIGHT.value,
        reply_markup=await keyboard(buttons),
    )


@dp.callback_query_handler(text_contains="max_height_")
async def max_height_callback(callback_query: types.CallbackQuery) -> None:
    """Handles the callback from the max height inline buttons, starts the generation process.
    Sends the preview and the archive.

    Args:
        callback_query (types.CallbackQuery): Callback, which triggered the handler.
    """
    await log_event(callback_query)

    max_height = int(callback_query.data.rsplit("_", 1)[-1])
    session = sessions.get(callback_query.from_user.id)
    if not session:
        return

    session.dem_settings = generate.DemSettings(5, max_height)

    await bot.send_message(
        callback_query.from_user.id,
        Messages.GENERATION_STARTED.value,
        reply_markup=await keyboard(Buttons.MAIN_MENU.value),
    )

    preview, result = session.run()
    archive = types.InputFile(result)
    picture = types.InputFile(preview)
    await bot.send_photo(callback_query.from_user.id, picture)
    try:
        await bot.send_document(callback_query.from_user.id, archive)
    except Exception as e:
        logger.error(e)
        await bot.send_message(
            callback_query.from_user.id,
            Messages.FILE_TOO_LARGE.value,
            reply_markup=await keyboard(Buttons.MAIN_MENU.value),
        )


async def keyboard(
    buttons: list[str] | dict[str, str]
) -> ReplyKeyboardMarkup | InlineKeyboardMarkup:
    """Creates a keyboard with buttons depending on the input.
    If the input is a list, creates a ReplyKeyboardMarkup.
    If the input is a dict, creates an InlineKeyboardMarkup, where keys are callback_data and values are text.

    Args:
        buttons (list[str] | dict[str, str]): List or dict of buttons.

    Returns:
        ReplyKeyboardMarkup | InlineKeyboardMarkup: Keyboard with buttons.
    """
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
    """Logs the event.

    Args:
        data (types.Message | types.CallbackQuery): Data, which triggered the handler.
    """
    try:
        logger.debug(
            f"Message from {data.from_user.username} with telegram ID {data.from_user.id}: {data.text}"
        )
    except AttributeError:
        logger.debug(
            f"Callback from {data.from_user.username} with telegram ID {data.from_user.id}: {data.data}"
        )


if __name__ == "__main__":
    executor.start_polling(dp, allowed_updates=["message", "callback_query"])
