

from sqlalchemy.orm import Session
from app.db.models import IngestionJob


def create_job(db: Session, job_data: dict) -> IngestionJob:
    try:
        new_job = IngestionJob(**job_data)
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        return new_job
    except Exception:
        db.rollback()
        raise


def get_job_by_id(db: Session, job_id: int) -> IngestionJob | None:
    return db.query(IngestionJob).filter(IngestionJob.id == job_id).first()


def get_jobs_by_video_id(db: Session, video_id: int) -> list[IngestionJob]:
    return db.query(IngestionJob).filter(IngestionJob.video_id == video_id).order_by(IngestionJob.created_at.desc()).all()



def update_job(db: Session, job_id: int, update_data: dict) -> IngestionJob | None:
    job = get_job_by_id(db, job_id)

    if job is None:
        return None

    allowed_fields = {"status", "retry_count", "error_message"}

    try:
        for key, value in update_data.items():
            if key not in allowed_fields:
                raise ValueError(f"Invalid update field: {key}")

            setattr(job, key, value)

        db.commit()
        db.refresh(job)

        return job
    except Exception:
        db.rollback()
        raise


def delete_job(db: Session, job_id: int) -> bool:
    job = get_job_by_id(db, job_id)

    if job is None:
        return False

    try:
        db.delete(job)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise