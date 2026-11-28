
import logging

from app.db.session import SessionLocal
from app.db.models import IngestionJobStatus, VideoStatus
from app.db.repositories import job_repository, video_repository
from app.ingestion.pipeline import VideoIngestionPipeline


logger = logging.getLogger(__name__)


def process_ingestion_job(job_id: int) -> dict | None:
    """
    Process one pending video ingestion job.

    The worker manages its own database session because it runs
    independently of the API request's database session.
    """

    db = SessionLocal()

    try:
        # 1. Fetch job
        job = job_repository.get_job_by_id(db, job_id)

        if job is None:
            logger.error("Ingestion job %s not found.", job_id)
            return None

        # Avoid processing an already completed or running job
        if job.status != IngestionJobStatus.PENDING:
            logger.warning(
                "Skipping job %s because its status is %s.",
                job_id,
                job.status,
            )
            return None

        # 2. Fetch associated video
        video = video_repository.get_video_by_id(db, job.video_id)

        if video is None:
            raise ValueError(f"Video {job.video_id} not found.")

        # 3. Validate video ownership
        if video.user_id is None:
            raise ValueError(
                f"Video {video.id} has no assigned owner. "
                "Cannot process ingestion."
            )

        user_id = video.user_id

        # 4. Mark job and video as processing
        job_repository.update_job(
            db,
            job_id,
            {
                "status": IngestionJobStatus.PROCESSING,
                "error_message": None,
            },
        )

        video_repository.update_video(
            db,
            video.id,
            {"status": VideoStatus.PROCESSING},
        )

        # 5. Run ingestion pipeline with verified owner ID
        pipeline = VideoIngestionPipeline()

        result = pipeline.ingest_video(
            video_id=video.id,
            youtube_video_id=video.youtube_video_id,
            user_id=user_id,
        )

        # 6. Mark job and video as completed
        job_repository.update_job(
            db,
            job_id,
            {"status": IngestionJobStatus.COMPLETED},
        )

        video_repository.update_video(
            db,
            video.id,
            {"status": VideoStatus.COMPLETED},
        )

        logger.info(
            "Ingestion job %s completed successfully. Chunks: %s",
            job_id,
            result["total_chunks"],
        )

        return result

    except Exception as exc:
        logger.exception("Ingestion job %s failed.", job_id)

        try:
            job = job_repository.get_job_by_id(db, job_id)

            if job is not None:
                job_repository.update_job(
                    db,
                    job_id,
                    {
                        "status": IngestionJobStatus.FAILED,
                        "retry_count": job.retry_count + 1,
                        "error_message": str(exc)[:5000],
                    },
                )

                video_repository.update_video(
                    db,
                    job.video_id,
                    {"status": VideoStatus.FAILED},
                )

        except Exception:
            logger.exception(
                "Could not update failure status for job %s.",
                job_id,
            )

        return None

    finally:
        db.close()
