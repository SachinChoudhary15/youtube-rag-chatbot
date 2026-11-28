


from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings
from app.embeddings.base import BaseEmbedding


@lru_cache(maxsize=1)
def get_embedding_client():
    return HuggingFaceEmbeddings(
        model_name=settings.HF_EMBEDDING_MODEL,
        model_kwargs={
            "device": settings.HF_EMBEDDING_DEVICE,
        },
        encode_kwargs={
            "batch_size": settings.HF_EMBEDDING_BATCH_SIZE,
            "normalize_embeddings": settings.HF_EMBEDDING_NORMALIZE,
        },
    )


class HuggingFaceEmbedding(BaseEmbedding):

    def __init__(self):
        self.client = get_embedding_client()

    @property
    def embedding_dimension(self) -> int:
        return settings.QDRANT_VECTOR_SIZE

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.client.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.client.embed_query(text)
