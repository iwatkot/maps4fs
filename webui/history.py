import json
import os
from time import time

from config import HISTORY_FILE, HISTORY_INTERVAL, HISTORY_LIMIT


def get_history(force: bool = False) -> dict[str, int]:
    """Get the history from the history file.
    History file is a dictionary where the key is a lat, lot coordinates and the value
    is the number of times that the generation of for those coordinates was requested.
    The dictionary is also contains a key "created" with the epoch time of the creation of the file.

    Arguments:
        force (bool): Whether to force the creation of a new history file.

    Returns:
        dict[str, int]: The history.
    """

    def load_history() -> dict:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)

    if force or not os.path.isfile(HISTORY_FILE):
        history = null_history()
    else:
        history = load_history()
        created = history.get("created")
        if not created or created + HISTORY_INTERVAL < int(time()):
            history = null_history()

    save_history(history)
    return history


def save_history(history: dict) -> None:
    """Save the history dictionary to the history file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def null_history() -> dict[tuple[float, float] | str, int]:
    """Return a null history."""
    return {"created": int(time())}


def add_entry(lat: float, lon: float) -> None:
    """Add an entry to the history.

    Arguments:
        lat (float): The latitude.
        lon (float): The longitude.
    """
    history = get_history()
    key = get_coordinates_key(lat, lon)
    if key in history:
        history[key] += 1
    else:
        history[key] = 1

    save_history(history)


def get_count(lat: float, lon: float) -> int:
    """Get the count of the number of times that the generation of the coordinates was requested.

    Arguments:
        lat (float): The latitude.
        lon (float): The longitude.

    Returns:
        int: The count.
    """
    history = get_history()
    key = get_coordinates_key(lat, lon)
    return history.get(key, 0)


def get_coordinates_key(lat: float, lon: float) -> str:
    """Get the key for the coordinates in the history.

    Arguments:
        lat (float): The latitude.
        lon (float): The longitude.

    Returns:
        str: The key.
    """
    lat = round(lat, 4)
    lon = round(lon, 4)
    return f"{lat},{lon}"


def is_over_limit(lat: float, lon: float) -> bool:
    """Check if the generation of the coordinates was requested more than the limit.

    Arguments:
        lat (float): The latitude.
        lon (float): The longitude.

    Returns:
        bool: Whether the limit was reached.
    """
    return get_count(lat, lon) >= HISTORY_LIMIT
