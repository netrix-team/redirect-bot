from enum import IntEnum
from beanie import Document

from typing import Optional
from pydantic import BaseModel, Field


class ContentType(IntEnum):
    TEXT_ONLY = 1
    FILES_ONLY = 2
    EMBEDS_ONLY = 3

    TEXT_AND_FILES = 4
    TEXT_AND_EMBEDS = 5
    FILES_AND_EMBEDS = 6

    ALL_CONTENT = 7


class Settings(BaseModel):
    allowed_bots: bool = Field(False)
    content_type: ContentType = Field(ContentType.ALL_CONTENT)
    allowed_extensions: Optional[list[str]] = Field(None, description=(
        'If None, all files are allowed. If specified, for example: '
        '["png", ...], only files with the specified extensions are allowed.'
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
