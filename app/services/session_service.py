
from sqlalchemy.orm import Session

from app.core.exceptions import SessionNotFoundException
from app.db.repositories import session_repository
from app.services.video_service import get_video_service


def create_session_service(
    db: Session,
    video_id: int,
    session_name: str,
    user_id: int,
):
    video = get_video_service(db, video_id, user_id)

    session_data = {
        "video_id": video.id,
        "session_name": session_name,
    }

    return session_repository.create_session(db, session_data)


def get_session_service(
    db: Session,
    session_id: int,
    user_id: int,
):
    session = session_repository.get_session_by_id_for_user(
        db,
        session_id,
        user_id,
    )

    if not session:
        raise SessionNotFoundException(
            f"Session with ID {session_id} not found."
        )

    return session


def get_sessions_by_video_id_service(
    db: Session,
    video_id: int,
    user_id: int,
):
    get_video_service(db, video_id, user_id)

    return session_repository.get_sessions_by_video_id_for_user(
        db,
        video_id,
        user_id,
    )


def update_session_service(
    db: Session,
    session_id: int,
    update_data: dict,
    user_id: int,
):
    # Verify ownership before updating.
    session = get_session_service(db, session_id, user_id)

    updated_session = session_repository.update_session(
        db,
        session.id,
        update_data,
    )

    if not updated_session:
        raise SessionNotFoundException(
            f"Session with ID {session_id} not found."
        )

    return updated_session


def delete_session_service(
    db: Session,
    session_id: int,
    user_id: int,
):
    # Verify ownership before deleting.
    session = get_session_service(db, session_id, user_id)

    deleted = session_repository.delete_session(
        db,
        session.id,
    )

    if not deleted:
        raise SessionNotFoundException(
            f"Session with ID {session_id} not found."
        )

    return deleted
