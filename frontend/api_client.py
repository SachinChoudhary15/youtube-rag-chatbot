
from typing import Any

import httpx


class APIClientError(Exception):
    """Raised when the backend API request fails."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class APIClient:
    """Synchronous HTTP client for the YouTube RAG Chatbot backend."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        access_token: str | None = None,
        timeout: float = 120.0,
    ):
        if not base_url or not base_url.strip():
            raise ValueError("Backend base URL is required.")

        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
        )

        self.set_credentials(
            api_key=api_key,
            access_token=access_token,
        )

    def set_credentials(
        self,
        api_key: str | None = None,
        access_token: str | None = None,
    ) -> None:
        """Configure API key or JWT authentication."""

        self._client.headers.pop("X-API-Key", None)
        self._client.headers.pop("Authorization", None)

        if access_token and access_token.strip():
            self._client.headers["Authorization"] = (
                f"Bearer {access_token.strip()}"
            )
        elif api_key and api_key.strip():
            self._client.headers["X-API-Key"] = api_key.strip()

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Any:
        """Send an HTTP request and handle common API errors."""

        try:
            response = self._client.request(
                method,
                endpoint.lstrip("/"),
                **kwargs,
            )

        except httpx.TimeoutException as exc:
            raise APIClientError(
                "Backend request timed out. Please try again."
            ) from exc

        except httpx.RequestError as exc:
            raise APIClientError(
                "Could not connect to the backend. "
                "Check whether the API server is running."
            ) from exc

        if response.is_error:
            message = "Backend request failed."

            try:
                error_data = response.json()

                if isinstance(error_data, dict):
                    message = str(
                        error_data.get("detail")
                        or error_data.get("message")
                        or message
                    )
                else:
                    message = str(error_data)

            except ValueError:
                if response.text.strip():
                    message = response.text.strip()[:500]

            raise APIClientError(
                message=message,
                status_code=response.status_code,
            )

        if response.status_code == 204 or not response.content:
            return None

        try:
            return response.json()
        except ValueError as exc:
            raise APIClientError(
                "Backend returned an invalid JSON response.",
                status_code=response.status_code,
            ) from exc

    # Authentication

    def register(self, email: str, password: str) -> dict:
        return self._request(
            "POST",
            "/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

    def login(self, email: str, password: str) -> dict:
        return self._request(
            "POST",
            "/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

    # Videos

    def create_video(self, youtube_video_id: str, title: str) -> dict:
        return self._request(
            "POST",
            "/videos",
            json={
                "youtube_video_id": youtube_video_id,
                "title": title,
            },
        )

    def get_videos(self) -> list[dict]:
        return self._request("GET", "/videos")

    def get_video(self, video_id: int) -> dict:
        return self._request("GET", f"/videos/{video_id}")

    def delete_video(self, video_id: int) -> None:
        self._request("DELETE", f"/videos/{video_id}")

    # Sessions

    def create_session(self, video_id: int, session_name: str) -> dict:
        return self._request(
            "POST",
            "/sessions",
            json={
                "video_id": video_id,
                "session_name": session_name,
            },
        )

    def get_video_sessions(self, video_id: int) -> list[dict]:
        return self._request("GET", f"/videos/{video_id}/sessions")

    def get_session(self, session_id: int) -> dict:
        return self._request("GET", f"/sessions/{session_id}")

    def update_session(self, session_id: int, session_name: str) -> dict:
        return self._request(
            "PATCH",
            f"/sessions/{session_id}",
            json={"session_name": session_name},
        )

    def delete_session(self, session_id: int) -> None:
        self._request("DELETE", f"/sessions/{session_id}")

    # Chat

    def send_message(
        self,
        session_id: int,
        question: str,
        top_k: int | None = None,
    ) -> dict:
        payload = {"question": question}

        if top_k is not None:
            payload["top_k"] = top_k

        return self._request(
            "POST",
            f"/sessions/{session_id}/chat",
            json=payload,
        )

    def get_messages(self, session_id: int) -> list[dict]:
        return self._request("GET", f"/sessions/{session_id}/messages")

    # Lifecycle

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
