
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship

from app.db.base import Base


# USER MODEL
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    videos = relationship(
        "Video",
        back_populates="user",
        cascade="all, delete-orphan",
    )


# VIDEO PROCESSING STATUS
class VideoStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# VIDEO MODEL
class Video(Base):
    __tablename__ = "videos"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "youtube_video_id",
            name="uq_video_user_youtube_id",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Nullable temporarily to preserve existing database records.
    # We will enforce ownership before completing authentication.
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    youtube_video_id = Column(
        String(255),
        nullable=False,
        index=True,
    )

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    channel_title = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    thumbnail_url = Column(Text, nullable=True)

    status = Column(
        Enum(
            VideoStatus,
            name="video_status",
            values_callable=lambda enum_cls: [
                member.value for member in enum_cls
            ],
        ),
        default=VideoStatus.PENDING,
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="videos")

    chat_sessions = relationship(
        "ChatSession",
        back_populates="video",
        cascade="all, delete-orphan",
    )

    ingestion_jobs = relationship(
        "IngestionJob",
        back_populates="video",
        cascade="all, delete-orphan",
    )


# CHAT SESSION MODEL
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    session_name = Column(String(255), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    chat_messages = relationship(
        "ChatMessage",
        back_populates="chat_session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

    video = relationship("Video", back_populates="chat_sessions")


# CHAT MESSAGE MODEL
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer,
        ForeignKey("chat_sessions.id"),
        nullable=False,
        index=True,
    )

    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    chat_session = relationship(
        "ChatSession",
        back_populates="chat_messages",
    )


# INGESTION JOB STATUS
class IngestionJobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# INGESTION JOB MODEL
class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)

    status = Column(
        Enum(
            IngestionJobStatus,
            name="ingestion_job_status",
            values_callable=lambda enum_cls: [
                member.value for member in enum_cls
            ],
        ),
        default=IngestionJobStatus.PENDING,
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)

    video = relationship("Video", back_populates="ingestion_jobs")
