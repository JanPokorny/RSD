import os
from pathlib import Path

DATA_PATH = Path(os.environ.get("RSD_DATA_PATH", "./data/"))
TTS_PATH = Path(os.environ.get("RSD_TTS_PATH", "./tmp/"))
MPD_SOCKET_PATH = Path(os.environ.get("RSD_MPD_SOCKET_PATH", "/tmp/mpd.socket"))

CHOSEN_MODELS = [
    os.environ.get("RSD_TTS_MODEL", "tts_models/cs/cv/vits"),
]
VOICE_MODELS = {
    f"TTS_MODEL_{i}": fs for i, fs in enumerate(CHOSEN_MODELS)
}

AUDIO_PATH = DATA_PATH / "audio"
BACKGROUND_PATH = DATA_PATH / "background"

DEFAULT_TEXT = os.environ.get("RSD_DEFAULT_TEXT", "Milí účastníci Dedikace, ")
REPEAT_ANNOUNCEMENT_JOINER_TEXT = os.environ.get("RSD_REPEAT_ANNOUNCEMENT_JOINER_TEXT", "Opakuji hlášení.")
