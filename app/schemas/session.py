


from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


# SESSION CREATE SCHEMA
class SessionCreate(BaseModel):
    video_id: int = Field(
        ...,
        gt=0,
        description="Database ID of the selected YouTube video.",
    )

    session_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the chat session.",
    )

    @field_validator("session_name")
    @classmethod
    def validate_session_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Session name cannot be empty.")

        return value


# SESSION UPDATE SCHEMA
class SessionUpdate(BaseModel):
    session_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    @field_validator("session_name")
    @classmethod
    def validate_session_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Session name cannot be empty.")

        return value


# SESSION RESPONSE SCHEMA
class SessionResponse(BaseModel):
    id: int
    video_id: int
    session_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
