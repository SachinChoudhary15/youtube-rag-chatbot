


import re


def clean_transcript_text(text: str) -> str:
    """
    Clean transcript text by normalizing whitespace and removing
    unwanted control characters.
    """

    if not isinstance(text, str):
        raise TypeError("Transcript text must be a string.")

    # Remove unwanted control characters while preserving normal whitespace.
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Normalize multiple spaces, tabs and newlines.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def preprocess_transcript(
    transcript_segments: list[dict],
) -> list[dict]:
    """
    Clean transcript segments while preserving their metadata
    and timestamps.
    """

    if not isinstance(transcript_segments, list):
        raise TypeError("Transcript segments must be a list.")

    cleaned_segments = []

    for segment in transcript_segments:

        if not isinstance(segment, dict):
            raise TypeError("Each transcript segment must be a dictionary.")

        cleaned_text = clean_transcript_text(segment.get("text", ""))

        if not cleaned_text:
            continue

        cleaned_segment = {
            **segment,
            "text": cleaned_text,
        }

        cleaned_segments.append(cleaned_segment)

    return cleaned_segments
