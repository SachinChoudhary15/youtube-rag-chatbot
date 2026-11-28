from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    """Create and return a cached Qdrant client."""

    return QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY or None,
        timeout=30,
    )


def check_qdrant_connection() -> bool:
    """Check whether Qdrant server is accessible."""

    client = get_qdrant_client()
    client.get_collections()
    return True


def create_collection() -> None:
    """Create the Qdrant collection and ensure required payload indexes."""

    client = get_qdrant_client()
    collection_name = settings.QDRANT_COLLECTION_NAME

    if not client.collection_exists(collection_name):
        distance = getattr(
            models.Distance,
            settings.QDRANT_DISTANCE.upper(),
            None,
        )

        if distance is None:
            raise ValueError(
                f"Unsupported Qdrant distance: {settings.QDRANT_DISTANCE}"
            )

        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=settings.QDRANT_VECTOR_SIZE,
                distance=distance,
            ),
        )

    collection_info = client.get_collection(collection_name)
    payload_schema = collection_info.payload_schema or {}

    if "video_id" not in payload_schema:
        client.create_payload_index(
            collection_name=collection_name,
            field_name="video_id",
            field_schema=models.PayloadSchemaType.INTEGER,
            wait=True,
        )