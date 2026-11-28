
import streamlit as st

from frontend.api_client import APIClient, APIClientError
from frontend.auth import require_authentication


st.title("🕘 Chat History")


def load_all_sessions(api_client: APIClient) -> list[dict]:
    """Load all chat sessions belonging to the authenticated user."""

    all_sessions = []

    videos = api_client.get_videos()

    for video in videos:
        video_id = video.get("id")

        if video_id is None:
            continue

        sessions = api_client.get_video_sessions(video_id)

        for session in sessions:
            session["video_title"] = video.get("title", "Unknown Video")
            session["youtube_video_id"] = video.get(
                "youtube_video_id", ""
            )
            all_sessions.append(session)

    all_sessions.sort(
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )

    return all_sessions


def display_messages(
    api_client: APIClient,
    session_id: int,
) -> None:
    """Display messages belonging to the selected session."""

    try:
        messages = api_client.get_messages(session_id)

        if not messages:
            st.info("No messages found in this conversation.")
            return

        for message in messages:
            role = message.get("role", "unknown").capitalize()
            content = message.get("content", "")
            created_at = message.get("created_at", "")

            with st.chat_message(
                "assistant" if role.lower() == "assistant" else "user"
            ):
                st.markdown(f"**{role}**")
                st.write(content)

                if created_at:
                    st.caption(created_at)

    except APIClientError as exc:
        st.error(f"Could not load messages: {exc}")


def rename_session(
    api_client: APIClient,
    session_id: int,
    new_name: str,
) -> None:
    """Rename a conversation."""

    new_name = new_name.strip()

    if not new_name:
        st.error("Conversation name cannot be empty.")
        return

    try:
        api_client.update_session(
            session_id=session_id,
            session_name=new_name,
        )

        st.success("Conversation renamed successfully!")
        st.rerun()

    except APIClientError as exc:
        st.error(f"Could not rename conversation: {exc}")


def delete_session(
    api_client: APIClient,
    session_id: int,
) -> None:
    """Delete a conversation."""

    try:
        api_client.delete_session(session_id)

        if st.session_state.get("selected_session_id") == session_id:
            st.session_state.pop("selected_session_id", None)

        st.success("Conversation deleted successfully!")
        st.rerun()

    except APIClientError as exc:
        st.error(f"Could not delete conversation: {exc}")


def main() -> None:
    api_client = require_authentication()

    if api_client is None:
        return

    st.subheader("Your Conversations")

    if st.button("🔄 Refresh History"):
        st.rerun()

    try:
        with st.spinner("Loading chat history..."):
            all_sessions = load_all_sessions(api_client)

    except APIClientError as exc:
        st.error(f"Could not load chat history: {exc}")
        return

    if not all_sessions:
        st.info("You haven't started any conversations yet.")
        return

    st.metric("Total Conversations", len(all_sessions))

    session_options = {
        session["id"]: (
            f"{session.get('session_name') or 'Untitled Conversation'} "
            f"— {session.get('video_title', 'Unknown Video')}"
        )
        for session in all_sessions
    }

    session_ids = list(session_options.keys())

    selected_session_id = st.selectbox(
        "Select a conversation",
        options=session_ids,
        format_func=lambda session_id: session_options[session_id],
        key="history_session_selector",
    )

    selected_session = next(
        (
            session
            for session in all_sessions
            if session["id"] == selected_session_id
        ),
        None,
    )

    if selected_session is None:
        st.warning("Selected conversation could not be found.")
        return

    st.divider()

    st.subheader(
        selected_session.get("session_name") or "Untitled Conversation"
    )

    st.write(
        f"**Video:** {selected_session.get('video_title', 'Unknown Video')}"
    )

    youtube_video_id = selected_session.get("youtube_video_id")

    if youtube_video_id:
        st.markdown(
            f"[▶️ Watch YouTube Video]"
            f"(https://www.youtube.com/watch?v={youtube_video_id})"
        )

    created_at = selected_session.get("created_at")

    if created_at:
        st.caption(f"Created: {created_at}")

    session_id = selected_session["id"]

    with st.expander("✏️ Rename Conversation"):
        with st.form(key=f"rename_form_{session_id}"):
            new_name = st.text_input(
                "New conversation name",
                value=selected_session.get("session_name") or "",
            )

            rename_submitted = st.form_submit_button("Rename")

            if rename_submitted:
                rename_session(api_client, session_id, new_name)

    with st.expander("🗑️ Delete Conversation"):
        confirm_delete = st.checkbox(
            "I understand this conversation will be permanently deleted.",
            key=f"confirm_delete_{session_id}",
        )

        if st.button(
            "Delete Conversation",
            key=f"delete_session_{session_id}",
            disabled=not confirm_delete,
        ):
            delete_session(api_client, session_id)

    st.divider()

    st.subheader("Conversation Messages")
    display_messages(api_client, session_id)


main()
