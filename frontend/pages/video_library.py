
import streamlit as st

from frontend.api_client import APIClient, APIClientError
from frontend.auth import require_authentication


st.title("📚 Video Library")
st.write("Add and manage your YouTube videos.")

st.divider()


def display_video_status(status: str) -> None:
    """Display video ingestion status."""

    status = str(status).upper()

    status_styles = {
        "PENDING": "🟡 Pending",
        "PROCESSING": "🔵 Processing",
        "COMPLETED": "🟢 Completed",
        "FAILED": "🔴 Failed",
    }

    st.write(status_styles.get(status, f"⚪ {status}"))


def add_video_form(api_client: APIClient) -> None:
    """Display the form for adding a YouTube video."""

    st.subheader("➕ Add New Video")

    with st.form("add_video_form", clear_on_submit=True):
        youtube_video_id = st.text_input(
            "YouTube Video ID",
            placeholder="Example: Gfr50f6ZBvo",
            help="Enter the YouTube video's ID, not its full URL.",
        )

        title = st.text_input(
            "Video Title",
            placeholder="Enter video title",
        )

        submitted = st.form_submit_button(
            "Add Video",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            if not youtube_video_id.strip():
                st.error("Please enter a YouTube Video ID.")

            elif not title.strip():
                st.error("Please enter a video title.")

            else:
                try:
                    with st.spinner("Registering video..."):
                        video = api_client.create_video(
                            youtube_video_id=youtube_video_id.strip(),
                            title=title.strip(),
                        )

                    st.success(
                        f"Video registered successfully! Video ID: {video['id']}"
                    )
                    st.rerun()

                except APIClientError as exc:
                    st.error(f"Could not add video: {exc}")


def display_video_library(api_client: APIClient) -> None:
    """Fetch and display registered videos."""

    st.subheader("🎬 Your Videos")

    if st.button("🔄 Refresh Videos"):
        st.rerun()

    try:
        with st.spinner("Loading videos..."):
            videos = api_client.get_videos()

    except APIClientError as exc:
        st.error(f"Could not load videos: {exc}")
        return

    if not videos:
        st.info("No videos found. Add your first YouTube video above.")
        return

    st.caption(f"Total videos: {len(videos)}")

    for video in videos:
        video_id = video.get("id")
        title = video.get("title") or "Untitled Video"
        youtube_id = video.get("youtube_video_id", "N/A")
        status = video.get("status", "UNKNOWN")

        with st.container(border=True):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"**{title}**")
                st.caption(f"YouTube ID: {youtube_id}")
                st.caption(f"Database Video ID: {video_id}")

            with col2:
                display_video_status(status)

            if video.get("channel_title"):
                st.caption(f"Channel: {video['channel_title']}")

            if video.get("thumbnail_url"):
                st.image(
                    video["thumbnail_url"],
                    width=220,
                )

            if video.get("description"):
                with st.expander("Video Description"):
                    st.write(video["description"])

            if str(status).upper() == "FAILED":
                st.warning(
                    "Video ingestion failed. Automatic retry is not "
                    "currently available."
                )

            if video_id is not None:
                with st.expander("Video Actions"):
                    if st.button(
                        "Delete Video",
                        key=f"delete_video_{video_id}",
                        type="secondary",
                    ):
                        try:
                            api_client.delete_video(int(video_id))
                            st.success("Video deleted successfully.")
                            st.rerun()

                        except APIClientError as exc:
                            st.error(f"Could not delete video: {exc}")


def main() -> None:
    """Video Library page entry point."""

    api_client = require_authentication()

    if api_client is None:
        return

    add_video_form(api_client)

    st.divider()

    display_video_library(api_client)


main()
