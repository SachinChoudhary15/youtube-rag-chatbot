
from sqlalchemy.orm import Session

from app.db.repositories import video_repository, job_repository
from app.core.exceptions import VideoNotFoundException
from app.db.models import IngestionJobStatus, VideoStatus
from app.vectorstore.repository import VectorRepository


def create_video_service(
    db: Session,
    youtube_video_id: str,
    title: str,
    user_id: int,
):
    video_data = {
        "youtube_video_id": youtube_video_id,
        "title": title,
        "user_id": user_id,
    }

    existing_video = video_repository.get_video_by_youtube_id_for_user(
        db,
        youtube_video_id,
        user_id,
    )

    if existing_video:
        return existing_video

    return video_repository.create_video(db, video_data)


def get_video_service(
    db: Session,
    video_id: int,
    user_id: int,
):
    video = video_repository.get_video_by_id_for_user(
        db,
        video_id,
        user_id,
    )

    if not video:
        raise VideoNotFoundException(
            f"Video with ID {video_id} not found."
        )

    return video


def get_video_by_youtube_id_service(
    db: Session,
    youtube_video_id: str,
    user_id: int,
):
    video = video_repository.get_video_by_youtube_id_for_user(
        db,
        youtube_video_id,
        user_id,
    )

    if not video:
        raise VideoNotFoundException(
            f"Video with YouTube ID {youtube_video_id} not found."
        )

    return video


def get_all_videos_service(
    db: Session,
    user_id: int,
):
    return video_repository.get_all_videos_for_user(db, user_id)


def update_video_service(
    db: Session,
    video_id: int,
    update_data: dict,
    user_id: int,
):
    video = video_repository.get_video_by_id_for_user(
        db,
        video_id,
        user_id,
    )

    if not video:
        raise VideoNotFoundException(
            f"Video with ID {video_id} not found."
        )

    return video_repository.update_video(
        db,
        video_id,
        update_data,
    )


def delete_video_service(
    db: Session,
    video_id: int,
    user_id: int,
):
    video = video_repository.get_video_by_id_for_user(
        db,
        video_id,
        user_id,
    )

    if not video:
        raise VideoNotFoundException(
            f"Video with ID {video_id} not found."
        )

    # Prevent deletion while ingestion is active.
    jobs = job_repository.get_jobs_by_video_id(db, video_id)

    active_jobs = [
        job
        for job in jobs
        if job.status in (
            IngestionJobStatus.PENDING,
            IngestionJobStatus.PROCESSING,
        )
    ]

    if video.status == VideoStatus.PROCESSING or active_jobs:
        raise ValueError(
            "Cannot delete video while ingestion is pending or processing."
        )

    # Delete Qdrant vectors first.
    vector_repository = VectorRepository(load_embedding_model=False)
    vector_repository.delete_chunks_by_video_id(
        video_id=video_id,
        user_id=user_id,
    )

    # Delete database records after successful vector cleanup.
    return video_repository.delete_video(db, video_id)
