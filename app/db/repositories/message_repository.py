
from sqlalchemy.orm import Session

from app.db.models import ChatMessage


def create_message(
    db: Session,
    message_data: dict,
    commit: bool = True,
) -> ChatMessage:
    try:
        new_message = ChatMessage(**message_data)
        db.add(new_message)

        if commit:
            db.commit()
            db.refresh(new_message)
        else:
            db.flush()

        return new_message

    except Exception:
        db.rollback()
        raise


def get_message_by_id(db: Session, message_id: int) -> ChatMessage | None:
    return db.query(ChatMessage).filter(
        ChatMessage.id == message_id
    ).first()


def get_messages_by_session_id(
    db: Session,
    session_id: int,
) -> list[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


def delete_message(db: Session, message_id: int) -> bool:
    message = get_message_by_id(db, message_id)

    if message is None:
        return False

    try:
        db.delete(message)
        db.commit()
        return True

    except Exception:
        db.rollback()
        raise
