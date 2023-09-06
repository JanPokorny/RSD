import hashlib
from pathlib import Path
import asyncio

from TTS.api import TTS
from moviepy.editor import CompositeAudioClip, AudioFileClip, afx

from RSD import config


tts: TTS | None = None


def tts_to_file(text: str, file_path: Path) -> None:
    global tts
    low_vol_out_path = file_path.with_stem(file_path.stem + "_lowvol")
    if tts is None:
        tts = TTS(config.TTS_MODEL)
    tts.tts_to_file(text=text, file_path=str(low_vol_out_path))
    AudioFileClip(str(low_vol_out_path)) \
        .fx(afx.audio_normalize) \
        .fx(afx.volumex, 2.0) \
        .write_audiofile(str(file_path))
    low_vol_out_path.unlink()


def read_to_file(text: str, repeat: bool, background_path: Path | None) -> str:
    text = f"{text}\n\n{config.REPEAT_ANNOUNCEMENT_JOINER_TEXT}\n\n{text}" if repeat else text
    path_nobg = output_file_path(text, background_path=None)
    if not path_nobg.is_file():
        tts_to_file(text, path_nobg)
    path_nobg.touch()

    path_bg = None
    if background_path is not None:
        path_bg = output_file_path(text, background_path=background_path)
        if not path_bg.is_file():
            fg_clip = AudioFileClip(str(path_nobg))
            bg_clip = AudioFileClip(str(background_path)) \
                .fx(afx.audio_loop, duration=fg_clip.duration) \
                .fx(afx.audio_normalize) \
                .fx(afx.volumex, 0.2) \
                .fx(afx.audio_fadeout, duration=2.0)
            CompositeAudioClip([fg_clip, bg_clip]) \
                .set_duration(fg_clip.duration) \
                .write_audiofile(str(path_bg), fps=fg_clip.fps)
        path_bg.touch()

    return str((path_bg or path_nobg).resolve())


async def read_to_file_async(text: str, repeat: bool, background_path: Path | None) -> str:
    return await asyncio.get_event_loop().run_in_executor(None, read_to_file, text, repeat, background_path)


# HELPERS
##########

def output_file_path(text: str, background_path: Path | None) -> Path:
    digest = hashlib.sha256(text.encode('utf-8')).hexdigest()[0:10]
    background_name = background_path.stem if background_path is not None else "nobg"
    return config.TTS_PATH / f"tts_{digest}_{background_name}.wav"

