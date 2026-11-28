

from sqlalchemy.orm import Session
from app.db.models import Video

def create_video(db: Session, video_data: dict) -> Video:

    try:
        new_video = Video(**video_data)
        db.add(new_video)
        db.commit()
        db.refresh(new_video)
        return new_video

    except Exception:
        db.rollback()
        raise

def get_video_by_id(db: Session, video_id: int) -> Video | None:

    return db.query(Video).filter(Video.id == video_id).first()

def get_video_by_youtube_id(db: Session, youtube_video_id: str) -> Video | None:

    return db.query(Video).filter(Video.youtube_video_id == youtube_video_id).first()

def get_all_videos(db: Session) -> list[Video]:

    return db.query(Video).all()




def update_video(db: Session, video_id: int, update_data: dict) -> Video | None:

    video = get_video_by_id(db, video_id)

    if video is None:
        return None

    allowed_fields = {
        "title",
        "description",
        "channel_title",
        "published_at",
        "thumbnail_url",
        "status",
    }

    try:
        for key, value in update_data.items():
            if key not in allowed_fields:
                raise ValueError(f"Invalid update field: {key}")

            setattr(video, key, value)

        db.commit()
        db.refresh(video)

        return video

    except Exception:
        db.rollback()
        raise

def delete_video(db: Session, video_id: int) -> bool:

    video = get_video_by_id(db, video_id)

    if video is None:
        return False

    try:
        db.delete(video)
        db.commit()
        return True

    except Exception:
        db.rollback()
        raise



def get_video_by_id_for_user(
    db: Session,
    video_id: int,
    user_id: int,
) -> Video | None:
    return (
        db.query(Video)
        .filter(
            Video.id == video_id,
            Video.user_id == user_id,
        )
        .first()
    )


def get_video_by_youtube_id_for_user(
    db: Session,
    youtube_video_id: str,
    user_id: int,
) -> Video | None:
    return (
        db.query(Video)
        .filter(
            Video.youtube_video_id == youtube_video_id,
            Video.user_id == user_id,
        )
        .first()
    )


def get_all_videos_for_user(
    db: Session,
    user_id: int,
) -> list[Video]:
    return (
        db.query(Video)
        .filter(Video.user_id == user_id)
        .all()
    )
