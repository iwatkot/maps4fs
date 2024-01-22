from enum import Enum


class Messages(Enum):
    START = (
        "Hello, I'm a bot that can generate map templates for Farming Simulator\.\n\n"
        "To get started, use the menu below\."
    )
    MENU_CHANGED = "You're in the {section} section now."
    GITHUB = (
        "Feel free to contribute to the [project on GitHub](https://github.com/iwatkot/maps4fs)\."
    )
    COFFEE = (
        "If you like my work, you can [buy me a coffee](https://www.buymeacoffee.com/iwatkot0)\."
    )


class Buttons(Enum):
    GENERATE = "🗺️ Generate new map"
    GITHUB = "🐙 Open on GitHub"
    COFFEE = "☕ Buy me a coffee"

    MAIN_MENU = [GENERATE, GITHUB, COFFEE]
    CANCEL = "❌ Cancel"
