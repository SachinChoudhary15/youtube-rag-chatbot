
from app.core.logging import logger


class CustomException(Exception):

    def __init__(self, message: str, status_code: int = 400, error_code: str = "APPLICATION_ERROR", details: dict | None = None):
        super().__init__(message)

        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

        logger.error(f"{self.error_code}: {self.message} "f"(Status Code: {self.status_code})")


class VideoNotFoundException(CustomException):
    def __init__(self, message: str = "Video not found"):
        super().__init__(message=message, status_code=404, error_code="VIDEO_NOT_FOUND")



class InvalidInputException(CustomException):
    def __init__(self, message: str = "Invalid input"):
        super().__init__(message=message, status_code=400, error_code="INVALID_INPUT")



class TranscriptNotAvailableException(CustomException):
    def __init__(self, message: str = "Transcript not available"):
        super().__init__(message=message, status_code=404, error_code="TRANSCRIPT_NOT_AVAILABLE")


class VideoProcessingException(CustomException):
    def __init__(self, message: str = "Error processing video"):
        super().__init__(message=message, status_code=500,error_code="VIDEO_PROCESSING_ERROR")


class SessionNotFoundException(CustomException):
    def __init__(self, message: str = "Session not found"):
        super().__init__(message=message, status_code=404, error_code="SESSION_NOT_FOUND")

class MessageNotFoundException(CustomException):
    def __init__(self, message="Message not found"):
        super().__init__(message, status_code=404)


class RAGException(CustomException):
    def __init__(self, message: str = "Error in RAG process"):
        super().__init__(message=message, status_code=500, error_code="RAG_ERROR")
