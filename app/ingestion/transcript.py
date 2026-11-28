from youtube_transcript_api import YouTubeTranscriptApi

from app.core.config import settings


def normalize_transcript(transcript_data: list[dict]) -> list[dict]:
    """
    Normalize YouTube transcript segments into a consistent format.
    """

    normalized_segments = []

    for segment in transcript_data:
        text = segment.get("text", "").strip()

        if not text:
            continue

        start = float(segment["start"])
        duration = float(segment["duration"])

        if start < 0 or duration < 0:
            raise ValueError("Transcript timestamps cannot be negative.")

        normalized_segments.append(
            {
                "text": text,
                "start": start,
                "duration": duration,
                "end": start + duration,
            }
        )

    if not normalized_segments:
        raise ValueError("Transcript contains no valid text segments.")

    return normalized_segments


def fetch_transcript(
    video_id: str,
    language: str | None = None,
) -> list[dict]:
    """
    Fetch a YouTube video's transcript and normalize its segments.
    """

    if not video_id or not video_id.strip():
        raise ValueError("YouTube video ID cannot be empty.")

    language = language or settings.YOUTUBE_LANGUAGE

    youtube_api = YouTubeTranscriptApi()

    fetched_transcript = youtube_api.fetch(
        video_id.strip(),
        languages=[language],
    )

    transcript_data = fetched_transcript.to_raw_data()

    return normalize_transcript(transcript_data)
