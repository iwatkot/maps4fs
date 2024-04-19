from enum import Enum


class Messages(Enum):
    """Messages, which are used in the bot."""

    START = (
        "Hello, I'm a bot that can generate map templates for Farming Simulator.\n\n"
        "To get started, use the menu below."
    )
    GITHUB = (
        "Feel free to contribute to the [project on GitHub](https://github.com/iwatkot/maps4fs)\."
    )
    COFFEE = (
        "If you like my work, you can [buy me a coffee](https://www.buymeacoffee.com/iwatkot0)\."
    )

    CANCELLED = "The operation has been cancelled."

    ENTER_COORDINATES = (
        "Enter the coordinates of the center of the map\."
        "The coordinates are latitude and longitude separated by a comma\.\n\n"
        "For example: `45\.2602, 19\.8086`\n\n"
        "You can obtain them by right\-clicking on the map in [Google Maps](https://www.google.com/maps)\."
    )
    WRONG_COORDINATES = (
        "Please enter the coordinates in the correct format\.\n\n"
        "For example: `45\.2602, 19\.8086`\n\n"
    )

    SELECT_MAP_SIZE = (
        "Select the size of the map.\n\n"
        "🟢 work fine on most devices.\n"
        "🟡 require a decent device.\n"
        "🔴 require a powerful device and not recommended.\n\n"
    )

    SELECT_MAX_HEIGHT = (
        "Select the maximum height of the map.\n"
        "It's recommended to use smaller values for flatlands and larger values for mountains."
    )

    GENERATION_STARTED = "Map generation has been started. It may take a while."
    FILE_TOO_LARGE = "The map is too large to send it via Telegram. Please, lower the map size."


class Buttons(Enum):
    """Buttons, which are used in the bot menu."""

    GENERATE = "🗺️ Generate new map"
    GITHUB = "🐙 Open on GitHub"
    COFFEE = "☕ Buy me a coffee"

    MAIN_MENU = [GENERATE, GITHUB, COFFEE]
    CANCEL = "❌ Cancel"
