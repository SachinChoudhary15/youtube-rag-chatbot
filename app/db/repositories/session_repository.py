
from sqlalchemy.orm import Session

from app.db.models import ChatSession, Video


def create_session(db: Session, session_data: dict) -> ChatSession:
    try:
        new_session = ChatSession(**session_data)
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session
    except Exception:
        db.rollback()
        raise


def get_session_by_id(db: Session, session_id: int) -> ChatSession | None:
    return (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id)
        .first()
    )


def get_session_by_id_for_user(
    db: Session,
    session_id: int,
    user_id: int,
) -> ChatSession | None:
    return (
        db.query(ChatSession)
        .join(Video, ChatSession.video_id == Video.id)
        .filter(
            ChatSession.id == session_id,
            Video.user_id == user_id,
        )
        .first()
    )


def get_sessions_by_video_id(db: Session, video_id: int) -> list[ChatSession]:
    return (
        db.query(ChatSession)
        .filter(ChatSession.video_id == video_id)
        .all()
    )


def get_sessions_by_video_id_for_user(
    db: Session,
    video_id: int,
    user_id: int,
) -> list[ChatSession]:
    return (
        db.query(ChatSession)
        .join(Video, ChatSession.video_id == Video.id)
        .filter(
            ChatSession.video_id == video_id,
            Video.user_id == user_id,
        )
        .all()
    )


def update_session(
    db: Session,
    session_id: int,
    update_data: dict,
) -> ChatSession | None:
    session = get_session_by_id(db, session_id)

    if session is None:
        return None

    allowed_fields = {"session_name"}

    try:
        for key, value in update_data.items():
            if key not in allowed_fields:
                raise ValueError(f"Invalid update field: {key}")

            setattr(session, key, value)

        db.commit()
        db.refresh(session)
        return session
    except Exception:
        db.rollback()
        raise


def delete_session(db: Session, session_id: int) -> bool:
    session = get_session_by_id(db, session_id)

    if session is None:
        return False

    try:
        db.delete(session)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
