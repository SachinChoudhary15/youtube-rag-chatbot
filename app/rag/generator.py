
import logging
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)
import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)



def is_retryable_error(exception: Exception) -> bool:
    """Identify temporary Gemini/API errors that are safe to retry."""

    if isinstance(
        exception,
        (
            httpx.TimeoutException,
            httpx.NetworkError,
            ConnectionError,
        ),
    ):
        return True

    status_code = (
        getattr(exception, "status_code", None)
        or getattr(exception, "code", None)
    )

    response = getattr(exception, "response", None)

    if status_code is None and response is not None:
        status_code = getattr(response, "status_code", None)

    retryable_status_codes = {429, 500, 502, 503, 504}

    if status_code in retryable_status_codes:
        return True

    message = str(exception).upper()

    retryable_messages = (
        "UNAVAILABLE",
        "RESOURCE_EXHAUSTED",
        "INTERNAL SERVER ERROR",
        "SERVICE UNAVAILABLE",
        "TOO MANY REQUESTS",
        "DEADLINE EXCEEDED",
        "READ TIMEOUT",
        "CONNECTION TIMEOUT",
    )

    return any(error in message for error in retryable_messages)



@lru_cache(maxsize=1)
def get_llm() -> ChatGoogleGenerativeAI:
    """
    Create and cache the Gemini language model client.
    """

    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured.")

    logger.info(
        "Initializing Gemini model: %s",
        settings.GEMINI_MODEL,
    )

    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=settings.GEMINI_TEMPERATURE,
        max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
        timeout=60,
        max_retries=0,
    )


class AnswerGenerator:
    """Generate answers using the Gemini language model."""

    def __init__(self, llm=None) -> None:
        self.llm = llm if llm is not None else get_llm()

    @retry(
        retry=retry_if_exception(is_retryable_error),
        wait=wait_exponential(
            multiplier=2,
            min=2,
            max=20,
        ),
        stop=stop_after_attempt(4),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _invoke_with_retry(self, prompt: str):
        """Invoke Gemini with retries for temporary API failures."""

        return self.llm.invoke(prompt)

    def generate(self, prompt: str) -> str:
        """
        Generate an answer from a formatted prompt.
        """

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        response = self._invoke_with_retry(prompt.strip())

        answer = response.content

        if isinstance(answer, str):
            result = answer.strip()

        elif isinstance(answer, list):
            result = " ".join(
                item["text"].strip()
                for item in answer
                if isinstance(item, dict)
                and isinstance(item.get("text"), str)
                and item["text"].strip()
            ).strip()

        else:
            result = ""

        if not result:
            raise ValueError("Gemini returned an empty response.")

        return result
