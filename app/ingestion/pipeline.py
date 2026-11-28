
from app.ingestion.transcript import fetch_transcript
from app.ingestion.preprocessing import preprocess_transcript
from app.ingestion.chunking import split_transcript_into_chunks
from app.vectorstore.repository import VectorRepository


class VideoIngestionPipeline:
    """Orchestrates the complete YouTube video ingestion workflow."""

    def __init__(self, vector_repository: VectorRepository | None = None):
        self.vector_repository = vector_repository or VectorRepository()

    @staticmethod
    def _validate_inputs(
        video_id: int,
        youtube_video_id: str,
        user_id: int,
    ) -> None:
        """Validate database video ID, YouTube video ID, and user ID."""

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

        if (
            not isinstance(youtube_video_id, str)
            or not youtube_video_id.strip()
        ):
            raise ValueError("youtube_video_id cannot be empty.")

        youtube_video_id = youtube_video_id.strip()

        if len(youtube_video_id) != 11:
            raise ValueError("Invalid YouTube video ID.")

    def ingest_video(
        self,
        video_id: int,
        youtube_video_id: str,
        user_id: int,
    ) -> dict:
        """Fetch, preprocess, chunk, and store a video's transcript."""

        self._validate_inputs(
            video_id=video_id,
            youtube_video_id=youtube_video_id,
            user_id=user_id,
        )

        youtube_video_id = youtube_video_id.strip()

        # Step 1: Fetch YouTube transcript
        transcript_segments = fetch_transcript(youtube_video_id)

        if not transcript_segments:
            raise ValueError("No transcript available for this video.")

        # Step 2: Preprocess transcript
        cleaned_segments = preprocess_transcript(transcript_segments)

        if not cleaned_segments:
            raise ValueError("Transcript contains no valid text.")

        # Step 3: Split transcript into chunks
        documents = split_transcript_into_chunks(cleaned_segments)

        if not documents:
            raise ValueError("No chunks generated from the transcript.")

        # Step 4: Store chunks in Qdrant with user isolation
        total_chunks = self.vector_repository.upsert_chunks(
            documents=documents,
            video_id=video_id,
            youtube_video_id=youtube_video_id,
            user_id=user_id,
        )

        if total_chunks == 0:
            raise ValueError("No transcript chunks were stored.")

        # Step 5: Return ingestion result
        return {
            "video_id": video_id,
            "youtube_video_id": youtube_video_id,
            "user_id": user_id,
            "total_chunks": total_chunks,
            "status": "completed",
        }
