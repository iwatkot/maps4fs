import os

from rich.console import Console

console = Console()
WORKING_DIR = os.getcwd()
console.log(f"Working directory: {WORKING_DIR}")

DATA_DIR = os.path.join(WORKING_DIR, "data")
TEMPLATE_ARCHIVE = os.path.join(DATA_DIR, "map-template.zip")

if not os.path.isfile(TEMPLATE_ARCHIVE):
    raise FileNotFoundError(
        f"Template archive not found: {TEMPLATE_ARCHIVE}. Please clone the repository again."
    )
