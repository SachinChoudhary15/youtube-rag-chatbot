
from langchain_core.documents import Document

from app.rag.generator import AnswerGenerator
from app.rag.prompts import get_rag_prompt
from app.rag.citations import CitationBuilder
from app.rag.retriever import VideoRetriever


class RAGChain:
    """Coordinate retrieval, prompt construction, and answer generation."""

    def __init__(
        self,
        retriever: VideoRetriever | None = None,
        generator: AnswerGenerator | None = None,
    ) -> None:
        self.retriever = (
            retriever if retriever is not None else VideoRetriever()
        )
        self.generator = (
            generator if generator is not None else AnswerGenerator()
        )

    @staticmethod
    def _validate_inputs(
        question: str,
        video_id: int,
        user_id: int,
        chat_history: str,
    ) -> None:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty.")

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

        if not isinstance(chat_history, str):
            raise ValueError("chat_history must be a string.")

    @staticmethod
    def _format_context(documents: list[Document]) -> str:
        context_parts = []

        for index, document in enumerate(documents, start=1):
            metadata = document.metadata or {}

            source = f"[Source {index}]"

            start_time = metadata.get("start_time")
            end_time = metadata.get("end_time")

            if start_time is not None:
                source += f" [Start: {start_time}s]"

            if end_time is not None:
                source += f" [End: {end_time}s]"

            context_parts.append(
                f"{source}\n{document.page_content}"
            )

        return "\n\n".join(context_parts)

    def invoke(
        self,
        question: str,
        video_id: int,
        user_id: int,
        chat_history: str = "",
        top_k: int | None = None,
    ) -> dict:
        """Retrieve user-owned context and generate a grounded answer."""

        self._validate_inputs(
            question=question,
            video_id=video_id,
            user_id=user_id,
            chat_history=chat_history,
        )

        documents = self.retriever.retrieve(
            query=question.strip(),
            video_id=video_id,
            user_id=user_id,
            top_k=top_k,
        )

        if not documents:
            return {
                "answer": (
                    "I couldn't find relevant information about this "
                    "question in the selected video's transcript."
                ),
                "citations": [],
                "video_id": video_id,
            }

        context = self._format_context(documents)

        prompt = get_rag_prompt().format(
            chat_history=chat_history.strip(),
            context=context,
            question=question.strip(),
        )

        answer = self.generator.generate(prompt)

        return {
            "answer": answer,
            "citations": CitationBuilder.build(documents),
            "video_id": video_id,
        }
