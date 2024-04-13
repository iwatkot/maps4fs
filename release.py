import os
import zipfile

ARCHIVE_NAME = "maps4fs.zip"

release_directories = ["data", "src"]
release_files = [
    "requirements.txt",
    "run.ps1",
    "run.sh",
    "textures.json",
]


def main():
    with zipfile.ZipFile(ARCHIVE_NAME, "w") as zf:
        for directory in release_directories:
            for root, _, files in os.walk(directory):
                for file in files:
                    zf.write(os.path.join(root, file))

        for file in release_files:
            zf.write(file)

    print(f"Release archive created: {ARCHIVE_NAME}")


if __name__ == "__main__":
    main()
