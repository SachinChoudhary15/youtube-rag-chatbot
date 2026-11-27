
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.dependencies import get_current_user
from app.core.exceptions import (
    SessionNotFoundException,
    VideoNotFoundException,
)
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
)
from app.services.session_service import (
    create_session_service,
    get_session_service,
    get_sessions_by_video_id_service,
    update_session_service,
    delete_session_service,
)


router = APIRouter(tags=["Sessions"])


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a chat session",
)
def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_session_service(
            db=db,
            video_id=session_data.video_id,
            session_name=session_data.session_name,
            user_id=current_user.id,
        )
    except VideoNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/videos/{video_id}/sessions",
    response_model=list[SessionResponse],
    summary="Get sessions for a video",
)
def get_video_sessions(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return get_sessions_by_video_id_service(
            db=db,
            video_id=video_id,
            user_id=current_user.id,
        )
    except VideoNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Get session details",
)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return get_session_service(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
        )
    except SessionNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Rename a chat session",
)
def update_session(
    session_id: int,
    session_data: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return update_session_service(
            db=db,
            session_id=session_id,
            update_data={
                "session_name": session_data.session_name,
            },
            user_id=current_user.id,
        )
    except SessionNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chat session",
)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        delete_session_service(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
        )
    except SessionNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
