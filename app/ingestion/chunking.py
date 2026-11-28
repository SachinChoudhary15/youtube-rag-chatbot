



from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.core.config import settings


def split_transcript_into_chunks(transcript_segments: list[dict],) -> list[Document]:
    """
    Split transcript segments into chunks while preserving timestamps.

    Each chunk contains:
        - page_content
        - chunk_index
        - start_time
        - end_time
        - start_char
        - end_char
    """

    if not transcript_segments:
        return []

    if settings.CHUNK_OVERLAP >= settings.CHUNK_SIZE:
        raise ValueError(
            "CHUNK_OVERLAP must be smaller than CHUNK_SIZE."
        )

    # Combine transcript segments and track their character positions.
    combined_text = ""
    segment_positions = []

    for index, segment in enumerate(transcript_segments):
        text = segment["text"].strip()

        if not text:
            continue

        if "start" not in segment or "end" not in segment:
            raise ValueError(
                "Each transcript segment must contain start and end timestamps."
            )

        if combined_text:
            combined_text += " "

        segment_start = len(combined_text)
        combined_text += text
        segment_end = len(combined_text)

        segment_positions.append(
            {
                "segment_index": index,
                "start_char": segment_start,
                "end_char": segment_end,
                "start_time": float(segment["start"]),
                "end_time": float(segment["end"]),
            }
        )

    if not combined_text:
        return []

    # Initialize text splitter.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        add_start_index=True,
    )

    # Generate chunks with original character positions.
    split_documents = text_splitter.create_documents([combined_text])

    result = []

    for chunk_index, document in enumerate(split_documents):
        start_char = document.metadata["start_index"]
        end_char = start_char + len(document.page_content)

        # Find transcript segments overlapping this chunk.
        overlapping_segments = [
            segment
            for segment in segment_positions
            if (
                segment["start_char"] < end_char
                and segment["end_char"] > start_char
            )
        ]

        if not overlapping_segments:
            continue

        metadata = {
            "chunk_index": chunk_index,
            "start_time": overlapping_segments[0]["start_time"],
            "end_time": overlapping_segments[-1]["end_time"],
            "start_char": start_char,
            "end_char": end_char,
        }

        result.append(
            Document(
                page_content=document.page_content,
                metadata=metadata,
            )
        )

    return result
