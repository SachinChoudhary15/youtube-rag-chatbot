
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT.parent / ".env"


class Settings(BaseSettings):

    # APPLICATION CONFIGURATION
    APP_NAME: str = "YouTube RAG Chatbot"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # GEMINI LLM CONFIGURATION
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_TEMPERATURE: float = Field(default=0.2, ge=0.0, le=2.0)
    GEMINI_MAX_OUTPUT_TOKENS: int = Field(default=2048, gt=0)

    # HUGGING FACE EMBEDDINGS
    HF_EMBEDDING_MODEL: str = "BAAI/bge-m3"
    HF_EMBEDDING_DEVICE: str = "cpu"
    HF_EMBEDDING_BATCH_SIZE: int = Field(default=8, gt=0)
    HF_EMBEDDING_NORMALIZE: bool = True
    HF_TOKEN: str | None = None

    # DATABASE CONFIGURATION
    DATABASE_URL: str = "sqlite:///./youtube_rag.db"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = Field(default=5, gt=0)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0)

    # QDRANT VECTOR DATABASE
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_NAME: str = "youtube_transcripts"
    QDRANT_VECTOR_SIZE: int = Field(default=1024, gt=0)
    QDRANT_DISTANCE: str = "COSINE"

    # RAG CONFIGURATION
    CHUNK_SIZE: int = Field(default=1000, gt=0)
    CHUNK_OVERLAP: int = Field(default=150, ge=0)
    RETRIEVER_TOP_K: int = Field(default=5, gt=0)
    SIMILARITY_THRESHOLD: float = Field(default=0.5, ge=0.0, le=1.0)
    RAG_MAX_CONTEXT_TOKENS: int = Field(default=6000, gt=0)

    # YOUTUBE CONFIGURATION
    YOUTUBE_LANGUAGE: str = "en"
    YOUTUBE_TRANSCRIPT_ENABLED: bool = True
    YOUTUBE_MAX_VIDEO_DURATION_MINUTES: int = Field(default=240, gt=0)

    # SESSION & CHAT CONFIGURATION
    SESSION_EXPIRY_HOURS: int = Field(default=24, gt=0)
    MAX_CHAT_HISTORY_MESSAGES: int = Field(default=10, ge=0)
    MAX_MESSAGE_LENGTH: int = Field(default=5000, gt=0)

    # SECURITY CONFIGURATION
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    CORS_ORIGINS: str = "http://localhost:8501"
    RATE_LIMIT_PER_MINUTE: int = Field(default=30, gt=0)
    APP_API_KEY: str | None = None

    # LOGGING CONFIGURATION
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "logs/app.log"

    # WORKER CONFIGURATION
    WORKER_ENABLED: bool = False
    WORKER_CONCURRENCY: int = Field(default=1, gt=0)
    INGESTION_MAX_RETRIES: int = Field(default=3, ge=0)
    INGESTION_RETRY_DELAY: int = Field(default=5, ge=0)

    # FRONTEND CONFIGURATION
    BACKEND_BASE_URL: str = "http://127.0.0.1:8000"
    STREAMLIT_SERVER_PORT: int = 8501

    # CACHE CONFIGURATION
    REDIS_URL: str | None = None

    # MONITORING
    ENABLE_METRICS: bool = False
    ENABLE_REQUEST_LOGGING: bool = True

    # JWT AUTHENTICATION
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: Literal["HS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, le=1440)

    # JWT SECRET VALIDATION
    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret_key(cls, value: str) -> str:
        if len(value.encode("utf-8")) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must contain at least 32 bytes."
            )

        if value != value.strip():
            raise ValueError(
                "JWT_SECRET_KEY cannot contain surrounding whitespace."
            )

        return value

    # PRODUCTION SECURITY VALIDATION
    @model_validator(mode="after")
    def validate_production_security(self):
        if self.ENVIRONMENT == "production" and self.DEBUG:
            raise ValueError(
                "DEBUG must be False in production."
            )

        return self

    # PYDANTIC SETTINGS
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # HELPER PROPERTIES
    @property
    def allowed_hosts_list(self) -> list[str]:
        return [
            host.strip()
            for host in self.ALLOWED_HOSTS.split(",")
            if host.strip()
        ]

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


# CACHED SETTINGS INSTANCE
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
