import asyncio
from pathlib import Path

import pydantic

from RSD import tts, config


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

    async def get_url(self) -> str:
        return await tts.read_to_file_async(self.text, self.repeat, self.background_path)

    def summary(self) -> str:
        return f"🗣️ {self.text}"

    def to_dict(self) -> dict:
        return {
            "type": "tts",
            "text": self.text,
            "repeat": self.repeat,
            "background_path": str(self.background_path.resolve()) if self.background_path is not None else None,
        }

    @staticmethod
    def from_dict(data: dict) -> "PlayRequestTTSItem":
        return PlayRequestTTSItem(
            text=data['text'],
            repeat=data['repeat'],
            background_path=Path(data['background_path']) if data['background_path'] is not None else None,
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
        return " | ".join(request_item.summary() for request_item in self.items)

    def to_dict(self) -> dict:
        return {
            "items": [item.to_dict() for item in self.items],
            "pending": self.pending,
        }

    @staticmethod
    def from_dict(data: dict) -> "PlayRequest":
        return PlayRequest(
            items=[PlayRequestItem.from_dict(item) for item in data["items"]],
            pending=data["pending"],
        )
