from enum import IntEnum
from beanie import Document

from typing import Optional
from pydantic import BaseModel, Field


class ContentType(IntEnum):
    TEXT_ONLY = 1  # Только текст
    FILES_ONLY = 2  # Только файлы
    EMBEDS_ONLY = 3  # Только ембеды

    TEXT_AND_FILES = 4  # Текст и файлы
    TEXT_AND_EMBEDS = 5  # Текст и ембеды
    FILES_AND_EMBEDS = 6 # файлы и ембеды

    ALL_CONTENT = 7  # Всё содержимое


class Settings(BaseModel):
    allowed_bots: bool = Field(False)
    content_type: ContentType = Field(ContentType.ALL_CONTENT)
    allowed_extensions: Optional[list[str]] = Field(None, description=(
        'Если None, разрешены все файлы. Если указаны, например: ["png", ...]'
        'то разрешены только файлы с указанными расширениями.'
    ))


class TargetChannel(BaseModel):
    id: int = Field(...)
    name: str = Field(..., max_length=255)
    settings: Settings = Field(default_factory=Settings)


class SourceChannel(BaseModel):
    id: int = Field(...)
    name: str = Field(..., max_length=255)
    targets: list[TargetChannel] = Field(default=[])


class WhiteListElement(BaseModel):
    id: int = Field(...)
    name: str = Field(..., max_length=255)


class Guild(Document):
    id: int = Field(...)
    name: str = Field(..., max_length=255)
    owner: int = Field(...)

    channels: Optional[list[SourceChannel]] = Field([])
    whitelist: Optional[list[WhiteListElement]] = Field(default=[])

    class Settings:
        name = 'guilds'
