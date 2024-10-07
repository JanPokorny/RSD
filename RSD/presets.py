from pathlib import Path

from RSD import config
from RSD.models import PlayRequest, PlayRequestAudioItem, PlayRequestTTSItem


def find_audio_file(name: str) -> Path:
    file_path = Path(next((str(path.resolve()) for path in Path(config.DATA_PATH).glob(f"**/{name}.*"))))
    if file_path is None:
        raise FileNotFoundError(f"No audio file found for {name}")
    return Path(file_path)


QUICK_ACCESS = {
    'alarm': PlayRequest(items=[
        PlayRequestAudioItem(path=find_audio_file("budicek1")),
        PlayRequestAudioItem(path=find_audio_file("budicek2")),
        PlayRequestAudioItem(path=find_audio_file("budicek3"))
    ]),
    'directions_walk': PlayRequest(items=[PlayRequestAudioItem(path=find_audio_file("hra"))]),
    'directions_run': PlayRequest(items=[PlayRequestAudioItem(path=find_audio_file("hra"))]),
    'self_improvement': PlayRequest(items=[PlayRequestAudioItem(path=find_audio_file("hra"))]),
    'bakery_dining': PlayRequest(items=[PlayRequestAudioItem(path=find_audio_file("obed"))]),
    'dinner_dining': PlayRequest(items=[PlayRequestAudioItem(path=find_audio_file("vecere"))]),
}

BEGIN_JINGLE = PlayRequestAudioItem(path=find_audio_file("_begin"))
END_JINGLE = PlayRequestAudioItem(path=find_audio_file("_end"))

DEFAULT_PLAY_REQUEST = PlayRequest(items=[
    BEGIN_JINGLE,
    PlayRequestTTSItem(),
    END_JINGLE
])
