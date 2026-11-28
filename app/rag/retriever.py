
from langchain_core.documents import Document

from app.vectorstore.repository import VectorRepository


class VideoRetriever:
    """Retrieve relevant transcript chunks for a specific user's video."""

    def __init__(
        self,
        vector_repository: VectorRepository | None = None,
    ) -> None:
        self.vector_repository = (
            vector_repository
            if vector_repository is not None
            else VectorRepository()
        )

    def retrieve(
        self,
        query: str,
        video_id: int,
        user_id: int,
        top_k: int | None = None,
    ) -> list[Document]:
        """
        Retrieve semantically relevant transcript chunks.

        Args:
            query: User's question.
            video_id: Internal database video ID.
            user_id: Authenticated owner's database ID.
            top_k: Maximum number of chunks to retrieve.

        Returns:
            Relevant transcript chunks as LangChain Documents.

        Raises:
            ValueError: If query, video_id, user_id or top_k is invalid.
        """

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query cannot be empty.")

        if (
            not isinstance(video_id, int)
            or isinstance(video_id, bool)
            or video_id <= 0
        ):
            raise ValueError("video_id must be a positive integer.")

        if (
            not isinstance(user_id, int)
            or isinstance(user_id, bool)
            or user_id <= 0
        ):
            raise ValueError("user_id must be a positive integer.")

        return self.vector_repository.search_similar_chunks(
            query=query.strip(),
            video_id=video_id,
            user_id=user_id,
            top_k=top_k,
        )
