
from langchain_core.documents import Document


class CitationBuilder:
    """Build source citations from retrieved transcript documents."""

    @staticmethod
    def build(documents: list[Document]) -> list[dict]:
        citations = []

        for index, document in enumerate(documents, start=1):
            metadata = document.metadata or {}

            citation = {
                "source": index,
                "text": document.page_content,
                "youtube_video_id": metadata.get("youtube_video_id"),
                "chunk_index": metadata.get("chunk_index"),
                "start_time": metadata.get("start_time"),
                "end_time": metadata.get("end_time"),
                "score": metadata.get("score"),
            }

            youtube_video_id = citation["youtube_video_id"]
            start_time = citation["start_time"]

            if (
                isinstance(youtube_video_id, str)
                and youtube_video_id.strip()
                and isinstance(start_time, (int, float))
                and not isinstance(start_time, bool)
                and start_time >= 0
            ):
                citation["timestamp_url"] = (
                    f"https://www.youtube.com/watch?v="
                    f"{youtube_video_id}&t={int(start_time)}s"
                )

            citations.append(citation)

        return citations
