
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import IngestionJobStatus, VideoStatus, User
from app.db.repositories import job_repository, video_repository
from app.schemas.video import VideoCreate, VideoResponse
from app.services.video_service import (
    create_video_service,
    get_video_service,
    get_all_videos_service,
    delete_video_service,
)
from app.workers.ingestion_worker import process_ingestion_job
from app.core.exceptions import VideoNotFoundException
from app.dependencies import get_current_user


router = APIRouter(
    prefix="/videos",
    tags=["Videos"],
)


@router.post(
    "",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a YouTube video and start ingestion",
)
def create_video(
    video_data: VideoCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a video and schedule transcript ingestion."""

    try:
        # 1. Register or retrieve video for the authenticated user
        video = create_video_service(
            db=db,
            youtube_video_id=video_data.youtube_video_id,
            title=video_data.title,
            user_id=current_user.id,
        )

        # 2. Check existing ingestion jobs
        jobs = job_repository.get_jobs_by_video_id(
            db,
            video.id,
        )

        latest_job = jobs[0] if jobs else None

        # 3. Avoid duplicate processing
        if latest_job and latest_job.status in (
            IngestionJobStatus.PENDING,
            IngestionJobStatus.PROCESSING,
        ):
            return video

        # Avoid re-ingesting an already completed video
        if (
            latest_job
            and latest_job.status == IngestionJobStatus.COMPLETED
            and video.status == VideoStatus.COMPLETED
        ):
            return video

        # 4. Reset failed video before retry
        if video.status == VideoStatus.FAILED:
            video = video_repository.update_video(
                db,
                video.id,
                {"status": VideoStatus.PENDING},
            )

        # 5. Create ingestion job
        job = job_repository.create_job(
            db,
            {"video_id": video.id},
        )

        # 6. Schedule background processing
        background_tasks.add_task(
            process_ingestion_job,
            job.id,
        )

        return video

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register video or schedule ingestion.",
        ) from exc


@router.get(
    "",
    response_model=list[VideoResponse],
    summary="Get all videos",
)
def get_all_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return videos belonging to the authenticated user."""

    return get_all_videos_service(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{video_id}",
    response_model=VideoResponse,
    summary="Get video by ID",
)
def get_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a video belonging to the authenticated user."""

    try:
        return get_video_service(
            db=db,
            video_id=video_id,
            user_id=current_user.id,
        )

    except VideoNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a video",
)
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a video belonging to the authenticated user."""

    try:
        delete_video_service(
            db=db,
            video_id=video_id,
            user_id=current_user.id,
        )

    except VideoNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
