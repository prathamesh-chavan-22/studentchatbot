"""
Custom exception hierarchy for the Semantic Support Bot.

All domain-specific errors derive from BotError so they can be caught
at any layer and translated into appropriate user-facing responses.
"""


class BotError(Exception):
    """Base exception for all bot-related errors. Never raised directly."""
    code: str = "BOT_ERROR"
    user_message: str = "An unexpected error occurred. Please try again later."

    def __init__(self, message: str, *, original: Exception | None = None):
        super().__init__(message)
        self._original = original

    @property
    def original(self) -> Exception | None:
        return self._original


# ---------------------------------------------------------------------------
# Initialization / lifecycle errors
# ---------------------------------------------------------------------------

class ModelLoadError(BotError):
    """Raised when the sentence-transformer model fails to load."""
    code = "MODEL_LOAD_ERROR"
    user_message = "The AI model failed to load. Please contact support."


class CacheError(BotError):
    """Raised when cache operations fail (read, write, validation)."""
    code = "CACHE_ERROR"
    user_message = "Unable to access cached data. Rebuilding index..."


class CacheCorruptionError(CacheError):
    """Raised when cached data is detected as corrupted."""
    code = "CACHE_CORRUPTED"
    user_message = "Cache is corrupted. Rebuilding index..."


class IndexBuildError(BotError):
    """Raised when building the FAISS index fails."""
    code = "INDEX_BUILD_ERROR"
    user_message = "Failed to build the question index. Please contact support."


# ---------------------------------------------------------------------------
# Inference / runtime errors
# ---------------------------------------------------------------------------

class InferenceError(BotError):
    """Raised when model inference fails (batch or single)."""
    code = "INFERENCE_ERROR"
    user_message = "Unable to process your question right now. Please try again."


class InferenceTimeoutError(InferenceError):
    """Raised when model inference times out."""
    code = "INFERENCE_TIMEOUT"
    user_message = "Processing timed out. Please try again."


class BatcherError(BotError):
    """Raised when the async batcher encounters a problem."""
    code = "BATCHER_ERROR"
    user_message = "The query processing service is unavailable."


class BatcherNotRunningError(BatcherError):
    """Raised when the batcher worker is not running."""
    code = "BATCHER_NOT_RUNNING"
    user_message = "The processing service is not running. Please contact support."


# ---------------------------------------------------------------------------
# Knowledge-base / data errors
# ---------------------------------------------------------------------------

class KnowledgeBaseError(BotError):
    """Raised when the knowledge base is empty or inaccessible."""
    code = "KB_ERROR"
    user_message = "The knowledge base is currently unavailable."


class KnowledgeBaseEmptyError(KnowledgeBaseError):
    """Raised when the knowledge base has no entries."""
    code = "KB_EMPTY"
    user_message = "No questions are configured in the knowledge base."


class QAFileError(BotError):
    """Raised when the QA JSON file cannot be read or parsed."""
    code = "QA_FILE_ERROR"
    user_message = "Unable to load the question database. Please contact support."


class QAFileParseError(QAFileError):
    """Raised when the QA JSON file is malformed."""
    code = "QA_PARSE_ERROR"
    user_message = "The question database file is corrupted. Please contact support."


# ---------------------------------------------------------------------------
# Search / retrieval errors
# ---------------------------------------------------------------------------

class SearchError(BotError):
    """Raised when semantic search fails."""
    code = "SEARCH_ERROR"
    user_message = "Unable to search for an answer right now. Please try again."


class FaissIndexError(SearchError):
    """Raised when FAISS index operations fail."""
    code = "FAISS_INDEX_ERROR"
    user_message = "The search index is corrupted. Please contact support."


# ---------------------------------------------------------------------------
# Input validation errors
# ---------------------------------------------------------------------------

class ValidationError(BotError):
    """Raised when user input fails validation."""
    code = "VALIDATION_ERROR"
    user_message = "Your input could not be processed."


class EmptyInputError(ValidationError):
    """Raised when user input is empty or whitespace-only."""
    code = "EMPTY_INPUT"
    user_message = "Please enter a question."


class InputTooLongError(ValidationError):
    """Raised when user input exceeds the allowed length."""
    code = "INPUT_TOO_LONG"
    user_message = "Your question is too long. Please keep it under 500 characters."


class ContentModerationError(BotError):
    """Raised when content moderation fails internally."""
    code = "MODERATION_ERROR"
    user_message = "Unable to validate your message. Please try again."
