
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.dependencies import get_current_user
from app.core.exceptions import SessionNotFoundException, RAGException
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    MessageResponse,
)
from app.services.chat_service import send_message_service
from app.services.message_service import get_messages_by_session_id_service


router = APIRouter(tags=["Chat"])


@router.post(
    "/sessions/{session_id}/chat",
    response_model=ChatResponse,
    summary="Send a message and get an AI-generated answer",
)
def send_chat_message(
    session_id: int,
    chat_data: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return send_message_service(
            db=db,
            session_id=session_id,
            question=chat_data.question,
            user_id=current_user.id,
            top_k=chat_data.top_k,
        )
    except SessionNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except RAGException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[MessageResponse],
    summary="Get messages for a chat session",
)
def get_chat_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return get_messages_by_session_id_service(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
        )
    except SessionNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
