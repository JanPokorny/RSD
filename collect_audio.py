import os
import json
from pathlib import Path
from RSD import config

FORMATS = (".mp3", ".wav", ".mp4", ".ogg", ".idk")

AUDIO_FOLDER = config.AUDIO_PATH
BACKGROUND_FOLDER = config.BACKGROUND_PATH
OUTPUT_FILE = "RSD/generated_config.py"

AUDIO_DICK = dict[str, Path]


def inspect_folder(folder: Path) -> AUDIO_DICK:
    audios = {}
    for filename in os.listdir(folder):
        if filename.endswith(FORMATS):
            key = os.path.splitext(filename)[0]
            value = os.path.abspath(os.path.join(folder, filename))
            audios[key] = value
    return audios


def inspect_folders(folders: list[Path]):
    return {
        key: val for folder in folders for key, val in inspect_folder(folder).items()
    }


def generate_config(audios, output_file):
    config_content = (
        "# This file is generated. Do not change. In the end, it doesnt even matter.\n"
    )
    config_content += f"AUDIOS = {json.dumps(audios, indent=4)}"

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        f.write(config_content)


def start():
    audios = inspect_folders([AUDIO_FOLDER, BACKGROUND_FOLDER])
    generate_config(audios, OUTPUT_FILE)

    print(f"Config file generated at {OUTPUT_FILE}")


if __name__ == "__main__":
    start()
