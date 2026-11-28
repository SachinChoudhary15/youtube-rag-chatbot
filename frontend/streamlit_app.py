
import streamlit as st

from frontend.api_client import APIClient, APIClientError
from frontend.auth import clear_authentication, get_backend_url


st.set_page_config(
    page_title="YouTube RAG Chatbot",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_api_client() -> APIClient | None:
    """Initialize an unauthenticated client for public auth endpoints."""

    base_url = get_backend_url()

    if not base_url:
        st.error("Backend URL is not configured.")
        return None

    try:
        return APIClient(base_url=base_url)
    except ValueError as exc:
        st.error(f"Invalid backend configuration: {exc}")
        return None


def handle_login(api_client: APIClient, email: str, password: str) -> None:
    """Authenticate user and store JWT in Streamlit session state."""

    try:
        response = api_client.login(
            email=email.strip(),
            password=password,
        )

        access_token = response.get("access_token")

        if not access_token:
            st.error("Login failed: access token was not returned.")
            return

        st.session_state.access_token = access_token
        st.session_state.user = {"email": email.strip()}

        st.success("Login successful!")
        st.rerun()

    except APIClientError as exc:
        st.error(f"Login failed: {exc}")


def handle_registration(
    api_client: APIClient,
    email: str,
    password: str,
    confirm_password: str,
) -> None:
    """Register a new user and authenticate them."""

    email = email.strip()

    if password != confirm_password:
        st.error("Passwords do not match.")
        return

    if len(password) < 8:
        st.error("Password must contain at least 8 characters.")
        return

    try:
        api_client.register(
            email=email,
            password=password,
        )

        st.success("Account created successfully!")

        # Automatically log in after successful registration.
        handle_login(api_client, email, password)

    except APIClientError as exc:
        st.error(f"Registration failed: {exc}")


def render_authentication(api_client: APIClient) -> None:
    """Display login and registration forms."""

    st.subheader("Welcome to YouTube RAG Chatbot")
    st.write("Login or create an account to continue.")

    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input(
                "Email address",
                key="login_email",
            )

            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )

            submitted = st.form_submit_button(
                "Login",
                use_container_width=True,
            )

            if submitted:
                if not email.strip() or not password:
                    st.error("Please enter your email and password.")
                else:
                    handle_login(api_client, email, password)

    with signup_tab:
        with st.form("signup_form"):
            email = st.text_input(
                "Email address",
                key="signup_email",
            )

            password = st.text_input(
                "Password",
                type="password",
                key="signup_password",
            )

            confirm_password = st.text_input(
                "Confirm password",
                type="password",
                key="signup_confirm_password",
            )

            submitted = st.form_submit_button(
                "Create Account",
                use_container_width=True,
            )

            if submitted:
                if not email.strip() or not password or not confirm_password:
                    st.error("Please complete all fields.")
                else:
                    handle_registration(
                        api_client,
                        email,
                        password,
                        confirm_password,
                    )


def render_authenticated_home() -> None:
    """Display the authenticated application home screen."""

    user = st.session_state.get("user", {})
    email = user.get("email", "User")

    st.success(f"Logged in as {email}")

    st.subheader("Your YouTube RAG Workspace")

    st.write(
        "Ask questions about YouTube videos and get answers "
        "based on their actual transcripts."
    )

    st.divider()

    st.markdown("### Getting Started")

    st.markdown(
        """
        1. Open **Video Library** to add a YouTube video.
        2. Wait for transcript processing to complete.
        3. Open **Chat** to start asking questions.
        4. Visit **Chat History** to manage previous conversations.
        """
    )


def main() -> None:
    """Main Streamlit application entry point."""

    st.title("🎥 YouTube RAG Chatbot")

    with st.sidebar:
        st.header("⚙️ Account")

        if st.session_state.get("access_token"):
            user = st.session_state.get("user", {})
            st.caption(user.get("email", "Authenticated user"))

            if st.button("Logout", use_container_width=True):
                clear_authentication()
                st.rerun()
        else:
            st.caption("Not logged in")

    if st.session_state.get("access_token"):
        render_authenticated_home()
        return

    api_client = initialize_api_client()

    if api_client is None:
        return

    render_authentication(api_client)


if __name__ == "__main__":
    main()
