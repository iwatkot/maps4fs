import json
import os
import shutil
import threading
from time import sleep
from typing import Generator

import schedule
from config import (
    ARCHIVES_DIRECTORY,
    MAPS_DIRECTORY,
    OSMPS_DIRECTORY,
    QUEUE_FILE,
    QUEUE_INTERVAL,
    QUEUE_TIMEOUT,
    TEMP_DIRECTORY,
    create_dirs,
    is_public,
)

from maps4fs import Logger

logger = Logger(level="INFO", to_file=False)


def get_queue(force: bool = False) -> list[str]:
    """Get the queue from the queue file.
    If the queue file does not exist, create a new one with an empty queue.

    Arguments:
        force (bool): Whether to force the creation of a new queue file.

    Returns:
        list[str]: The queue.
    """
    if not os.path.isfile(QUEUE_FILE) or force:
        logger.debug("Queue will be reset.")
        save_queue([])
        return []
    with open(QUEUE_FILE, "r") as f:
        return json.load(f)


def get_queue_length() -> int:
    """Get the length of the queue.

    Returns:
        int: The length of the queue.
    """
    return len(get_queue())


def save_queue(queue: list[str]) -> None:
    """Save the queue to the queue file.

    Arguments:
        queue (list[str]): The queue to save to the queue file.
    """
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f)
    logger.debug("Queue set to %s.", queue)


def add_to_queue(session: str) -> None:
    """Add a session to the queue.

    Arguments:
        session (str): The session to add to the queue.
    """
    queue = get_queue()
    queue.append(session)
    save_queue(queue)
    logger.debug("Session %s added to the queue.", session)


def get_first_item() -> str | None:
    """Get the first item from the queue.

    Returns:
        str: The first item from the queue.
    """
    queue = get_queue()
    if not queue:
        return None
    return queue[0]


def get_position(session: str) -> int | None:
    """Get the position of a session in the queue.

    Arguments:
        session (str): The session to get the position of.

    Returns:
        int: The position of the session in the queue.
    """
    queue = get_queue()
    if session not in queue:
        return None
    return queue.index(session)


def remove_from_queue(session: str) -> None:
    """Remove a session from the queue.

    Arguments:
        session (str): The session to remove from the queue.
    """
    queue = get_queue()
    if session in queue:
        queue.remove(session)
        save_queue(queue)
        logger.debug("Session %s removed from the queue.", session)
    else:
        logger.debug("Session %s not found in the queue.", session)


def wait_in_queue(session: str) -> Generator[int, None, None]:
    """Wait in the queue until the session is the first item.

    Arguments:
        session (str): The session to wait for.
    """
    retries = QUEUE_TIMEOUT // QUEUE_INTERVAL
    logger.debug(
        "Starting to wait in the queue for session %s with maximum retries %s.", session, retries
    )

    termiation_thread = threading.Thread(target=start_termination, args=(session,))
    termiation_thread.start()

    for _ in range(retries):
        position = get_position(session)
        if position == 0 or position is None:
            logger.debug("Session %s is the first item in the queue.", session)
            return
        logger.debug("Session %s is in position %s in the queue.", session, position)
        yield position
        sleep(QUEUE_INTERVAL)


def start_termination(session: str) -> None:
    """Start the termination of a session.
    No matter if it was awaited, in queue or not, after a timeout it will be removed
    from the queue.

    Arguments:
        session (str): The session to terminate.
    """
    logger.debug("Session %s will be terminated after %s seconds.", session, QUEUE_TIMEOUT)
    sleep(QUEUE_TIMEOUT)
    remove_from_queue(session)


def auto_clean() -> None:
    """Automatically clean the directories."""
    if not is_public():
        return
    if get_queue_length() > 0:
        return

    to_clean = [ARCHIVES_DIRECTORY, MAPS_DIRECTORY, OSMPS_DIRECTORY, TEMP_DIRECTORY]
    for directory in to_clean:
        shutil.rmtree(directory, ignore_errors=True)

    create_dirs()


def run_scheduler():
    while True:
        schedule.run_pending()
        sleep(1)


if is_public():
    schedule.every(240).minutes.do(auto_clean)
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

get_queue(force=True)
