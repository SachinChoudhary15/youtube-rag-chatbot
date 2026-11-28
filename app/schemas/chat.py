

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime



# CHAT REQUEST SCHEMA
class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="User's question about the selected YouTube video.",
        examples=["What is Retrieval-Augmented Generation?"],
    )

    top_k: int | None = Field(
        default=None,
        ge=1,
        description="Maximum number of transcript chunks to retrieve.",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Question cannot be empty.")

        return value


# CITATION RESPONSE SCHEMA
class CitationResponse(BaseModel):
    source: int = Field(..., ge=1)
    text: str
    youtube_video_id: str | None = None
    chunk_index: int | None = Field(default=None, ge=0)
    start_time: float | None = Field(default=None, ge=0)
    end_time: float | None = Field(default=None, ge=0)
    score: float | None = None
    timestamp_url: str | None = None


# CHAT RESPONSE SCHEMA
class ChatResponse(BaseModel):
    answer: str
    session_id: int
    video_id: int
    citations: list[CitationResponse] = Field(default_factory=list)


# MESSAGE RESPONSE SCHEMA
class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
