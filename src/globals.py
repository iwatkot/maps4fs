import os
import shutil

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

OUTPUT_DIR = os.path.join(WORKING_DIR, "output")
console.log(f"Output directory: {OUTPUT_DIR}")
if not os.path.isdir(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)
    console.log("Output directory created.")
else:
    console.log("Output directory already exists and will be deleted.")
    shutil.rmtree(OUTPUT_DIR)
    os.mkdir(OUTPUT_DIR)

shutil.unpack_archive(TEMPLATE_ARCHIVE, OUTPUT_DIR)
console.log("Template archive unpacked.")
