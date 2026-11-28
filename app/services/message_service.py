
from sqlalchemy.orm import Session

from app.db.repositories import message_repository
from app.services.session_service import get_session_service
from app.core.exceptions import (
    SessionNotFoundException,
    MessageNotFoundException,
)


def create_message_service(
    db: Session,
    session_id: int,
    content: str,
    sender: str,
    user_id: int,
    commit: bool = True,
):
    session = get_session_service(db, session_id, user_id)

    message_data = {
        "session_id": session.id,
        "role": sender,
        "content": content,
    }

    if commit:
        return message_repository.create_message(db, message_data)

    return message_repository.create_message(
        db,
        message_data,
        commit=False,
    )


def get_message_service(
    db: Session,
    message_id: int,
    user_id: int,
):
    message = message_repository.get_message_by_id(db, message_id)

    if not message:
        raise MessageNotFoundException(
            f"Message with ID {message_id} not found."
        )

    # Verify that the message belongs to the authenticated user.
    get_session_service(db, message.session_id, user_id)

    return message


def get_messages_by_session_id_service(
    db: Session,
    session_id: int,
    user_id: int,
):
    session = get_session_service(db, session_id, user_id)

    return message_repository.get_messages_by_session_id(
        db,
        session.id,
    )


def delete_message_service(
    db: Session,
    message_id: int,
    user_id: int,
):
    # Verify ownership before deletion.
    get_message_service(db, message_id, user_id)

    deleted = message_repository.delete_message(db, message_id)

    if not deleted:
        raise MessageNotFoundException(
            f"Message with ID {message_id} not found."
        )

    return deleted
