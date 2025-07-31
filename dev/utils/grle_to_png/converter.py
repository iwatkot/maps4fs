import os
from pprint import pprint
from typing import Generator

from dev.utils.read_images.image_reader import normalize_and_color_map, read_image

# grleConverter.exe sample.grle -out sample.png
# CONVERTER_PATH = "dev/utils/grle_to_png/grleConverter.exe"
# DATA_DIRECTORY = "dev/utils/grle_to_png/data"

cwd = os.getcwd()
print(f"Current working directory: {cwd}")
GRLE_TO_PNG_DIRECTORY = os.path.join(cwd, "dev", "utils", "grle_to_png")
CONVERTER_PATH = os.path.join(GRLE_TO_PNG_DIRECTORY, "grleConverter.exe")
if not os.path.exists(CONVERTER_PATH):
    raise FileNotFoundError(f"Converter executable not found at: {CONVERTER_PATH}")
DATA_DIRECTORY = os.path.join(GRLE_TO_PNG_DIRECTORY, "data")


def grle_files(directory: str) -> Generator[str, None, None]:
    """Yield paths to .grle files in the specified directory.

    Args:
        directory (str): The directory to search for .grle files.

    Yields:
        str: Full path to each .grle file found in the directory.
    """
    if not os.path.isdir(directory):
        raise ValueError(f"The specified directory does not exist: {directory}")
    file_names = os.listdir(directory)
    print(f"Found {len(file_names)} files in directory: {directory}")
    for file_name in file_names:
        if file_name.endswith(".grle"):
            yield os.path.join(directory, file_name)


def switch_extension(file_path: str, new_extension: str) -> str:
    """Change the file extension of the given file path.

    Args:
        file_path (str): The original file path.
        new_extension (str): The new file extension to use.

    Returns:
        str: The file path with the new extension.
    """
    base = os.path.splitext(file_path)[0]
    return f"{base}.{new_extension}"


def convert_grle_to_png(grle_file: str) -> str:
    """Convert a .grle file to .png using the grleConverter executable.

    Args:
        grle_file (str): The path to the .grle file to convert.

    Returns:
        str: The path to the converted .png file.
    """
    output_file = switch_extension(grle_file, "png")
    command = f"{CONVERTER_PATH} {grle_file} -out {output_file}"
    os.system(command)
    return output_file


def convert_all_grle_to_png(directory: str) -> list[str]:
    """Convert all .grle files in the specified directory to .png.

    Args:
        directory (str): The directory containing .grle files.
    """
    outputs = []
    for grle_file in grle_files(directory):
        print(f"Converting {grle_file} to PNG...")
        outputs.append(convert_grle_to_png(grle_file))

    return outputs


def add_postfix(file_path: str, postfix: str) -> str:
    """Add a postfix to the file name before the extension.

    Args:
        file_path (str): The original file path.
        postfix (str): The postfix to add.

    Returns:
        str: The modified file path with the postfix added.
    """
    base, ext = os.path.splitext(file_path)
    return f"{base}_{postfix}{ext}"


if __name__ == "__main__":
    outputs = convert_all_grle_to_png(DATA_DIRECTORY)
    for output in outputs:
        pprint(read_image(output))
        colored_output = add_postfix(output, "colored")
        normalize_and_color_map(output, colored_output)
