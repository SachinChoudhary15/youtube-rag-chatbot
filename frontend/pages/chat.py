
import streamlit as st

from frontend.api_client import APIClient, APIClientError
from frontend.auth import require_authentication


st.title("💬 YouTube RAG Chat")
st.write("Ask questions about your YouTube videos.")

st.divider()


def load_completed_videos(api_client: APIClient) -> list[dict]:
    """Load videos that are ready for chatting."""

    videos = api_client.get_videos()

    return [
        video
        for video in videos
        if str(video.get("status", "")).upper() == "COMPLETED"
    ]


def create_new_session(
    api_client: APIClient,
    video_id: int,
    session_name: str,
) -> None:
    """Create a chat session for the selected video."""

    if not session_name.strip():
        st.error("Please enter a session name.")
        return

    try:
        session = api_client.create_session(
            video_id=video_id,
            session_name=session_name.strip(),
        )

        st.session_state.selected_session_id = session["id"]
        st.session_state.latest_citations = []
        st.session_state.citation_session_id = session["id"]

        st.success("New chat session created.")
        st.rerun()

    except APIClientError as exc:
        st.error(f"Could not create chat session: {exc}")


def display_citations(citations: list[dict]) -> None:
    """Display source citations for the latest answer."""

    if not citations:
        return

    with st.expander(f"📚 Sources ({len(citations)})"):
        for index, citation in enumerate(citations, start=1):
            st.markdown(f"**Source {index}**")

            source = citation.get("source")
            if source:
                st.caption(str(source))

            text = citation.get("text")
            if text:
                st.write(text)

            metadata = []

            if citation.get("chunk_index") is not None:
                metadata.append(f"Chunk: {citation['chunk_index']}")

            if citation.get("start_time") is not None:
                metadata.append(f"Start: {citation['start_time']}")

            if citation.get("end_time") is not None:
                metadata.append(f"End: {citation['end_time']}")

            if citation.get("score") is not None:
                metadata.append(f"Score: {citation['score']}")

            if metadata:
                st.caption(" | ".join(metadata))

            timestamp_url = citation.get("timestamp_url")

            if timestamp_url:
                st.markdown(
                    f"[▶ Open video at this source]({timestamp_url})"
                )

            if index < len(citations):
                st.divider()


def display_chat_history(
    api_client: APIClient,
    session_id: int,
) -> None:
    """Load and display messages from the selected session."""

    try:
        messages = api_client.get_messages(session_id)

    except APIClientError as exc:
        st.error(f"Could not load chat history: {exc}")
        return

    for message in messages:
        role = str(message.get("role", "assistant")).lower()

        if "user" in role:
            role = "user"
        else:
            role = "assistant"

        with st.chat_message(role):
            st.markdown(message.get("content", ""))

    # Display citations returned with the latest answer in this UI session.
    if (
        st.session_state.get("citation_session_id") == session_id
        and st.session_state.get("latest_citations")
    ):
        display_citations(st.session_state.latest_citations)


def main() -> None:
    """Main Chat page."""

    api_client = require_authentication()

    if api_client is None:
        return

    # 1. Load completed videos
    try:
        videos = load_completed_videos(api_client)

    except APIClientError as exc:
        st.error(f"Could not load videos: {exc}")
        return

    if not videos:
        st.info(
            "No completed videos available. "
            "Please add a video in Video Library and wait "
            "for its ingestion to complete."
        )
        return

    # 2. Video selection
    video_options = {
        video["id"]: video.get("title", "Untitled Video")
        for video in videos
    }

    selected_video_id = st.selectbox(
        "🎬 Select a video",
        options=list(video_options.keys()),
        format_func=lambda video_id: video_options[video_id],
        key="chat_video_selector",
    )

    st.divider()

    # 3. Load sessions for selected video
    try:
        sessions = api_client.get_video_sessions(selected_video_id)

    except APIClientError as exc:
        st.error(f"Could not load chat sessions: {exc}")
        return

    session_ids = [session["id"] for session in sessions]

    if st.session_state.get("selected_session_id") not in session_ids:
        st.session_state.selected_session_id = (
            session_ids[0] if session_ids else None
        )

    # 4. Session creation
    with st.expander("➕ Create New Chat", expanded=not sessions):
        session_name = st.text_input(
            "Chat session name",
            value="New Chat",
            key=f"new_session_name_{selected_video_id}",
        )

        if st.button(
            "Create Chat",
            type="primary",
            use_container_width=True,
        ):
            create_new_session(
                api_client,
                selected_video_id,
                session_name,
            )

    # 5. Existing session selection
    if sessions:
        st.subheader("Your Chat Sessions")

        session_labels = {
            session["id"]: session["session_name"]
            for session in sessions
        }

        current_session_id = st.selectbox(
            "Select a chat session",
            options=session_ids,
            index=session_ids.index(
                st.session_state.selected_session_id
            ),
            format_func=lambda session_id: session_labels[session_id],
            key=f"session_selector_{selected_video_id}",
        )

        st.session_state.selected_session_id = current_session_id

    else:
        st.info("Create a chat session to start asking questions.")
        return

    selected_session_id = st.session_state.selected_session_id

    st.divider()
    st.subheader("Conversation")

    # 6. Display existing messages
    display_chat_history(
        api_client,
        selected_session_id,
    )

    # 7. Send a new question
    question = st.chat_input(
        "Ask something about this video..."
    )

    if question:
        try:
            with st.spinner("Generating answer..."):
                response = api_client.send_message(
                    session_id=selected_session_id,
                    question=question,
                )

            st.session_state.latest_citations = (
                response.get("citations", [])
            )
            st.session_state.citation_session_id = selected_session_id

            st.rerun()

        except APIClientError as exc:
            st.error(f"Could not generate answer: {exc}")


main()
