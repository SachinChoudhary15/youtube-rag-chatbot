
from uuid import NAMESPACE_URL, uuid5

from langchain_core.documents import Document
from qdrant_client.http import models

from app.core.config import settings
from app.embeddings.huggingface_embeddings import HuggingFaceEmbedding
from app.vectorstore.qdrant_client import get_qdrant_client


class VectorRepository:
    """Repository for managing user-isolated video transcript vectors."""

    def __init__(self, load_embedding_model: bool = True):
        self.client = get_qdrant_client()
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.embedding_model = (
            HuggingFaceEmbedding()
            if load_embedding_model
            else None
        )

    @staticmethod
    def _validate_video_id(video_id: int) -> None:
        """Validate the internal database video ID."""

        if (
            not isinstance(video_id, int)
            or isinstance(video_id, bool)
            or video_id <= 0
        ):
            raise ValueError("video_id must be a positive integer.")

    @staticmethod
    def _validate_user_id(user_id: int) -> None:
        """Validate the authenticated database user ID."""

        if (
            not isinstance(user_id, int)
            or isinstance(user_id, bool)
            or user_id <= 0
        ):
            raise ValueError("user_id must be a positive integer.")

    def _get_point_ids_by_video_id(
        self,
        video_id: int,
        user_id: int,
    ) -> set[str | int]:
        """Retrieve existing point IDs for a user's specific video."""

        point_ids = set()
        offset = None

        while True:
            points, next_offset = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="video_id",
                            match=models.MatchValue(value=video_id),
                        ),
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id),
                        ),
                    ]
                ),
                limit=1000,
                offset=offset,
                with_payload=False,
                with_vectors=False,
            )

            for point in points:
                point_ids.add(point.id)

            if next_offset is None:
                break

            offset = next_offset

        return point_ids

    def _delete_point_ids(self, point_ids: set[str | int]) -> None:
        """Delete specific Qdrant points in batches."""

        point_ids = list(point_ids)

        for start in range(0, len(point_ids), 1000):
            batch = point_ids[start:start + 1000]

            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=batch,
                ),
                wait=True,
            )

    def upsert_chunks(
        self,
        documents: list[Document],
        video_id: int,
        youtube_video_id: str,
        user_id: int,
    ) -> int:
        """Upsert user-owned transcript chunks and remove stale chunks."""

        self._validate_video_id(video_id)
        self._validate_user_id(user_id)

        if not isinstance(youtube_video_id, str) or not youtube_video_id.strip():
            raise ValueError("youtube_video_id cannot be empty.")

        youtube_video_id = youtube_video_id.strip()

        if not isinstance(documents, list):
            raise TypeError("documents must be a list.")

        if not documents:
            return 0

        valid_documents = []

        for document in documents:
            if not isinstance(document, Document):
                raise TypeError("Each item must be a LangChain Document.")

            if not isinstance(document.page_content, str):
                raise TypeError("Document page_content must be a string.")

            if not isinstance(document.metadata, dict):
                raise TypeError("Document metadata must be a dictionary.")

            if document.page_content.strip():
                valid_documents.append(document)

        if not valid_documents:
            return 0

        chunk_indexes = []

        for document in valid_documents:
            chunk_index = document.metadata.get("chunk_index")

            if (
                not isinstance(chunk_index, int)
                or isinstance(chunk_index, bool)
                or chunk_index < 0
            ):
                raise ValueError(
                    "Every document must have a valid non-negative chunk_index."
                )

            chunk_indexes.append(chunk_index)

        if len(chunk_indexes) != len(set(chunk_indexes)):
            raise ValueError("Duplicate chunk_index values are not allowed.")

        if self.embedding_model is None:
            raise RuntimeError("Embedding model is not initialized.")

        texts = [document.page_content for document in valid_documents]

        vectors = self.embedding_model.embed_documents(texts)

        if len(vectors) != len(valid_documents):
            raise ValueError("Embedding count does not match document count.")

        points = []

        for document, vector in zip(valid_documents, vectors):
            if len(vector) != settings.QDRANT_VECTOR_SIZE:
                raise ValueError(
                    "Embedding dimension does not match Qdrant configuration."
                )

            chunk_index = document.metadata["chunk_index"]

            # Different users get different point IDs for the same video.
            point_id = str(
                uuid5(
                    NAMESPACE_URL,
                    f"{user_id}:{youtube_video_id}:{chunk_index}",
                )
            )

            payload = {
                **document.metadata,
                "video_id": video_id,
                "user_id": user_id,
                "youtube_video_id": youtube_video_id,
                "text": document.page_content,
            }

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            )

        # Fetch only this user's existing chunks for this video.
        existing_point_ids = self._get_point_ids_by_video_id(
            video_id=video_id,
            user_id=user_id,
        )

        new_point_ids = {point.id for point in points}

        # Upsert first. Do not delete old chunks if upsert fails.
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

        stale_point_ids = existing_point_ids - new_point_ids

        if stale_point_ids:
            self._delete_point_ids(stale_point_ids)

        return len(points)

    def search_similar_chunks(
        self,
        query: str,
        video_id: int,
        user_id: int,
        top_k: int | None = None,
    ) -> list[Document]:
        """Search semantically within a specific user's video."""

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Search query cannot be empty.")

        self._validate_video_id(video_id)
        self._validate_user_id(user_id)

        limit = (
            settings.RETRIEVER_TOP_K
            if top_k is None
            else top_k
        )

        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or limit <= 0
        ):
            raise ValueError("top_k must be a positive integer.")

        if self.embedding_model is None:
            raise RuntimeError("Embedding model is not initialized.")

        query_vector = self.embedding_model.embed_query(query.strip())

        if len(query_vector) != settings.QDRANT_VECTOR_SIZE:
            raise ValueError(
                "Query embedding dimension does not match Qdrant configuration."
            )

        search_results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="video_id",
                        match=models.MatchValue(value=video_id),
                    ),
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id),
                    ),
                ]
            ),
            limit=limit,
            score_threshold=settings.SIMILARITY_THRESHOLD,
            with_payload=True,
        ).points

        documents = []

        for result in search_results:
            payload = result.payload or {}
            text = payload.get("text", "")

            if not isinstance(text, str) or not text.strip():
                continue

            metadata = {
                key: value
                for key, value in payload.items()
                if key != "text"
            }

            metadata["score"] = result.score

            documents.append(
                Document(
                    page_content=text,
                    metadata=metadata,
                )
            )

        return documents

    def delete_chunks_by_video_id(
        self,
        video_id: int,
        user_id: int,
    ) -> None:
        """Delete only the authenticated user's chunks for a video."""

        self._validate_video_id(video_id)
        self._validate_user_id(user_id)

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="video_id",
                            match=models.MatchValue(value=video_id),
                        ),
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id),
                        ),
                    ]
                )
            ),
            wait=True,
        )

    def get_chunks_by_video_id(
        self,
        video_id: int,
        user_id: int,
    ) -> list[Document]:
        """Retrieve only the authenticated user's chunks for a video."""

        self._validate_video_id(video_id)
        self._validate_user_id(user_id)

        documents = []
        offset = None
        page_limit = 1000

        while True:
            scroll_results, next_offset = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="video_id",
                            match=models.MatchValue(value=video_id),
                        ),
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id),
                        ),
                    ]
                ),
                limit=page_limit,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            for point in scroll_results:
                payload = point.payload or {}
                text = payload.get("text", "")

                if not isinstance(text, str) or not text.strip():
                    continue

                metadata = {
                    key: value
                    for key, value in payload.items()
                    if key != "text"
                }

                documents.append(
                    Document(
                        page_content=text,
                        metadata=metadata,
                    )
                )

            if next_offset is None:
                break

            offset = next_offset

        return documents

    def count_chunks_by_video_id(
        self,
        video_id: int,
        user_id: int,
    ) -> int:
        """Count chunks belonging to a specific user's video."""

        self._validate_video_id(video_id)
        self._validate_user_id(user_id)

        count_result = self.client.count(
            collection_name=self.collection_name,
            count_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="video_id",
                        match=models.MatchValue(value=video_id),
                    ),
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id),
                    ),
                ]
            ),
            exact=True,
        )

        return count_result.count
