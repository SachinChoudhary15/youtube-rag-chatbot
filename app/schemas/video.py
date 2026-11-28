
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


# VIDEO CREATE SCHEMA
class VideoCreate(BaseModel):
    youtube_video_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="YouTube video ID.",
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="YouTube video title.",
    )

    @field_validator("youtube_video_id", "title")
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty.")

        return value


# VIDEO RESPONSE SCHEMA
class VideoResponse(BaseModel):
    id: int
    youtube_video_id: str
    title: str
    description: str | None = None
    channel_title: str | None = None
    published_at: datetime | None = None
    thumbnail_url: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
