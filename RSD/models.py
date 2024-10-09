import asyncio
from pathlib import Path

import pydantic
from TTS.api import TTS

from RSD import tts, config


TTS_MODELS = {key: TTS(val) for key, val in config.VOICE_MODELS.items()}


class PlayRequestItem(pydantic.BaseModel):
    async def get_url(self) -> str:
        pass

    def summary(self) -> str:
        pass

    def to_dict(self) -> dict:
        pass

    @staticmethod
    def from_dict(data) -> "PlayRequestItem":
        if data['type'] == 'tts':
            return PlayRequestTTSItem(**data)
        elif data['type'] == 'audio':
            return PlayRequestAudioItem(**data)
        else:
            raise ValueError(f"Unknown PlayRequestItem type: {data['type']}")


class PlayRequestTTSItem(PlayRequestItem):
    text: str = config.DEFAULT_TEXT
    repeat: bool = True
    background_path: Path | None = None
    voice_model: str = list(config.VOICE_MODELS.keys())[0]

    @staticmethod
    def make_custom(model: str) -> 'PlayRequestTTSItem':
        tmp = PlayRequestTTSItem()
        tmp.voice_model = model
        return tmp

    async def get_url(self) -> str:
        return await tts.read_to_file_async(
            self.text,
            self.repeat,
            self.background_path,
            TTS_MODELS[self.voice_model]
        )

    def summary(self) -> str:
        return f"🗣️ {self.text}"

    def to_dict(self) -> dict:
        return {
            "type": "tts",
            "text": self.text,
            "repeat": self.repeat,
            "background_path": str(self.background_path.resolve()) if self.background_path is not None else None,
            "model_name": self.voice_model,
        }

    @staticmethod
    def from_dict(data: dict) -> "PlayRequestTTSItem":
        return PlayRequestTTSItem(
            text=data['text'],
            repeat=data['repeat'],
            background_path=Path(data['background_path']) if data['background_path'] is not None else None,
            voice_model=data['voice_model'],
        )


class PlayRequestAudioItem(PlayRequestItem):
    path: Path | None = None

    async def get_url(self) -> str:
        return str(self.path.resolve())

    def summary(self) -> str:
        return f"🎵 {self.path.stem}"

    def to_dict(self) -> dict:
        return {
            "type": "audio",
            "path": str(self.path.resolve()),
        }

    @staticmethod
    def from_dict(data: dict) -> "PlayRequestAudioItem":
        return PlayRequestAudioItem(
            path=Path(data['path']),
        )


class PlayRequest(pydantic.BaseModel):
    items: list[PlayRequestItem]
    pending: bool = False
    delay_s: int = 0
    heading: str = ""

    async def get_urls(self) -> list[str]:
        try:
            self.pending = True
            return [
                url
                for url
                in await asyncio.gather(*(request_item.get_url() for request_item in self.items))
                if url is not None
            ]
        finally:
            self.pending = False

    def summary(self) -> str:
        cond_newline = "\n" if self.heading else ""
        return f'<span class="text-lg font-bold">{self.heading}</span>{cond_newline}' + " | ".join(request_item.summary() for request_item in self.items)

    def to_dict(self) -> dict:
        return {
            "items": [item.to_dict() for item in self.items],
            "pending": self.pending,
            "delay_s": self.delay_s,
            "heading": self.heading,
        }

    @staticmethod
    def from_dict(data: dict) -> "PlayRequest":
        return PlayRequest(
            items=[PlayRequestItem.from_dict(item) for item in data["items"]],
            pending=data["pending"],
            delay_s=data.get("delay_s", 0),
            heading=data.get("heading", ""),
        )
