"""Speech-to-text abstraction.

The application only ever deals with ``SpeechService``. Real deployments plug
an OpenAI (Whisper) provider in; development/tests use ``LocalSpeechService``,
a deterministic service that reads UTF-8 text from the uploaded payload so the
full voice pipeline is exercised offline.

Audio content itself is never stored by the API.
"""

from dataclasses import dataclass
from typing import Protocol

from app.core.config import get_settings
from app.core.errors import AppError


class SpeechServiceError(AppError):
    """Raised when no speech-to-text provider can transcribe the payload."""

    def __init__(self, message: str = "Speech-to-text is unavailable") -> None:
        super().__init__(message, code="VOICE_SERVICE_UNAVAILABLE", status_code=503)


@dataclass(frozen=True)
class Transcript:
    text: str
    language: str | None


class SpeechService(Protocol):
    name: str

    def transcribe(self, audio_bytes: bytes) -> Transcript:
        """Return the transcript of ``audio_bytes`` or raise SpeechServiceError."""
        ...


class LocalSpeechService:
    """Development-only provider.

    Decodes the uploaded payload as UTF-8 text. This lets the voice pipeline
    be demoed and tested without any external transcription service.
    """

    name = "local"

    def transcribe(self, audio_bytes: bytes) -> Transcript:
        try:
            text = audio_bytes.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise SpeechServiceError(
                "Speech-to-text is not configured. Type the transcript "
                "manually or set speech_provider=openai."
            ) from exc
        return Transcript(text=text, language="und")


class OpenAIWhisperService:
    """OpenAI Whisper provider (used when configured).

    The ``openai`` package is imported lazily: a missing dependency surfaces
    as a clear, user-facing ``VoiceServiceUnavailable`` error rather than an
    import crash at app startup.
    """

    name = "openai"

    def __init__(self, model: str, api_key: str) -> None:
        self._model = model
        self._api_key = api_key

    def transcribe(self, audio_bytes: bytes) -> Transcript:
        try:
            import openai

            client = openai.OpenAI(api_key=self._api_key)
        except ImportError as exc:
            raise SpeechServiceError(
                "The OpenAI provider is configured but the 'openai' package is not installed."
            ) from exc
        try:
            result = client.audio.transcriptions.create(
                model=self._model,
                file=("upload.mp3", audio_bytes, "audio/mpeg"),
            )
        except Exception as exc:
            raise SpeechServiceError(f"Speech provider error: {exc}") from exc
        return Transcript(text=result.text or "", language=getattr(result, "language", None))


def get_speech_service() -> SpeechService:
    settings = get_settings()
    if settings.speech_provider == "openai" and settings.openai_api_key:
        return OpenAIWhisperService(
            model=settings.openai_speech_model,
            api_key=settings.openai_api_key,
        )
    return LocalSpeechService()
