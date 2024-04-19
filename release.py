import os
import zipfile

ARCHIVE_PATH = os.path.join("/Users/iwatkot/Downloads", "maps4fs.zip")

release_directories = ["data", "maps4fs"]
release_files = [
    "requirements.txt",
    "run.ps1",
    "run.sh",
]


def main() -> None:
    with zipfile.ZipFile(ARCHIVE_PATH, "w") as zf:
        for directory in release_directories:
            for root, _, files in os.walk(directory):
                for file in files:
                    zf.write(os.path.join(root, file))

        for file in release_files:
            zf.write(file)

    print(f"Release archive created: {ARCHIVE_PATH}")


if __name__ == "__main__":
    main()
