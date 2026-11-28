
from sqlalchemy.orm import Session

from app.rag.chain import RAGChain
from app.services.session_service import get_session_service
from app.services.message_service import (
    create_message_service,
    get_messages_by_session_id_service,
)
from app.core.exceptions import RAGException


def send_message_service(
    db: Session,
    session_id: int,
    question: str,
    user_id: int,
    top_k: int | None = None,
) -> dict:
    """
    Generate a video-grounded answer and persist the conversation.
    Only the authenticated session owner can access this conversation.
    """

    # 1. Validate session ownership.
    session = get_session_service(db, session_id, user_id)

    # 2. Load only this owner's conversation history.
    previous_messages = get_messages_by_session_id_service(
        db=db,
        session_id=session_id,
        user_id=user_id,
    )

    chat_history = "\n".join(
        f"{message.role.capitalize()}: {message.content}"
        for message in previous_messages
    )

    # 3. Generate answer using user-isolated RAG.
    try:
        rag_chain = RAGChain()

        rag_result = rag_chain.invoke(
            question=question,
            video_id=session.video_id,
            user_id=user_id,
            chat_history=chat_history,
            top_k=top_k,
        )

        answer = rag_result["answer"]
        citations = rag_result.get("citations", [])

    except Exception as exc:
        raise RAGException(
            "Failed to generate an answer using the RAG pipeline."
        ) from exc

    # 4. Persist both messages in one transaction.
    try:
        create_message_service(
            db=db,
            session_id=session_id,
            content=question,
            sender="user",
            user_id=user_id,
            commit=False,
        )

        create_message_service(
            db=db,
            session_id=session_id,
            content=answer,
            sender="assistant",
            user_id=user_id,
            commit=False,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    # 5. Return response.
    return {
        "answer": answer,
        "session_id": session_id,
        "video_id": session.video_id,
        "citations": citations,
    }
