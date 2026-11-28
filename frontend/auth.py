
import os

import streamlit as st

from app.core.config import settings
from frontend.api_client import APIClient


def get_backend_url() -> str:
    """Get backend URL from Streamlit secrets, environment, or settings."""

    try:
        base_url = st.secrets.get("BACKEND_BASE_URL", "")
    except Exception:
        base_url = ""

    return (
        base_url
        or os.getenv("BACKEND_BASE_URL")
        or settings.BACKEND_BASE_URL
        or ""
    )


def _close_api_client(client: APIClient | None) -> None:
    """Safely close an existing API client."""

    if client is None:
        return

    try:
        client.close()
    except Exception:
        pass


def get_authenticated_api_client() -> APIClient | None:
    """Return a reusable API client authenticated with the current user's JWT."""

    access_token = st.session_state.get("access_token")

    if not access_token:
        return None

    base_url = get_backend_url().strip()

    if not base_url:
        st.error("Backend URL is not configured.")
        return None

    client_identity = (base_url, access_token)

    existing_client = st.session_state.get("api_client")
    existing_identity = st.session_state.get("_api_client_identity")

    # Reuse the existing client if the URL and token are unchanged.
    if existing_client is not None and existing_identity == client_identity:
        return existing_client

    # Close the previous client if the token or backend URL changed.
    _close_api_client(existing_client)

    st.session_state.pop("api_client", None)
    st.session_state.pop("_api_client_identity", None)

    try:
        api_client = APIClient(
            base_url=base_url,
            access_token=access_token,
        )

        st.session_state["api_client"] = api_client
        st.session_state["_api_client_identity"] = client_identity

        return api_client

    except Exception as exc:
        st.error(f"Could not initialize API client: {exc}")
        return None


def clear_authentication() -> None:
    """Close the API client and clear authentication and user-specific UI state."""

    # Close the current user's HTTP client.
    existing_client = st.session_state.get("api_client")
    _close_api_client(existing_client)

    # Clear authentication and client information.
    st.session_state.pop("access_token", None)
    st.session_state.pop("user", None)
    st.session_state.pop("api_client", None)
    st.session_state.pop("_api_client_identity", None)

    # Clear user-specific chat and selection state.
    user_state_keys = [
        "selected_session_id",
        "latest_citations",
        "citation_session_id",
        "history_session_selector",
        "selected_video_id",
        "video_selector",
        "session_selector",
    ]

    for key in user_state_keys:
        st.session_state.pop(key, None)


def require_authentication() -> APIClient | None:
    """Require login before allowing access to protected pages."""

    if not st.session_state.get("access_token"):
        st.warning("Please login to access this page.")
        st.info("Open the Home page and login to continue.")
        return None

    return get_authenticated_api_client()
