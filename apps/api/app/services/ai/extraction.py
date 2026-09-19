"""Structured-extraction providers.

``extract_from_transcript`` is the single entry point. The default provider is
``LocalExtractionProvider``: a deterministic, rule-based extractor used by
tests and offline demos. Real deployments pick ``OpenAIExtractionProvider`` via
``ai_provider=openai``.

Both providers return ``ExtractionResult`` after pydantic validation, so a
misbehaving upstream can never inject malformed observations.
"""

import re
from typing import Protocol

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.enums import ObservationType
from app.services.ai.prompts import EXTRACTION_PROMPT_VERSION, SYSTEM_PROMPT
from app.services.ai.schemas import ExtractedObservation, ExtractionOutput

_NUMBERS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


class ExtractionResult:
    """Validated extraction plus the AI metadata recorded on the report."""

    def __init__(
        self,
        *,
        output: ExtractionOutput,
        provider: str,
        model: str | None,
        model_version: str,
        confidence: float | None,
    ) -> None:
        self.output = output
        self.provider = provider
        self.model = model
        self.model_version = model_version
        self.confidence = confidence


class AIProviderError(AppError):
    """Raised when an AI provider cannot produce a valid extraction."""

    def __init__(self, message: str = "AI extraction failed") -> None:
        super().__init__(message, code="AI_EXTRACTION_FAILED", status_code=422)


class AIProvider(Protocol):
    provider_name: str
    model: str | None

    def extract(self, transcript: str, prompt_version: str) -> ExtractionOutput: ...


def _clamp_confidence(value: float) -> float:
    return max(0.0, min(1.0, value))


class LocalExtractionProvider:
    """Deterministic keyword-based extraction.

    Explicit numbers and clear statements are extracted with high confidence;
    vague mentions are kept with low confidence and never coerced into a
    number. Anything not mentioned is reported in ``not_mentioned``.
    """

    provider_name = "local"
    model = "local-rules-v1"

    _TYPE_ORDER = (
        ObservationType.PAIN,
        ObservationType.SLEEP,
        ObservationType.FOOD_INTAKE,
        ObservationType.MOBILITY,
        ObservationType.MOOD,
        ObservationType.BREATHING,
        ObservationType.ENERGY,
        ObservationType.OTHER,
    )

    def __init__(self) -> None:
        self._hands = _compile_handlers()

    def extract(self, transcript: str, prompt_version: str) -> ExtractionOutput:
        text = f" {transcript.strip().lower()} "
        observations: list[ExtractedObservation] = []
        for obs_type in self._TYPE_ORDER:
            handler = self._hands.get(obs_type)
            if handler is None:
                continue
            extracted = handler(text)
            if extracted is not None:
                observations.append(extracted)

        mentioned = {obs.type.value for obs in observations}
        not_mentioned = [obs.value for obs in self._TYPE_ORDER if obs.value not in mentioned]

        mentioned_labels = [obs.type.value for obs in observations]
        if mentioned_labels:
            summary = "Update mentions: " + ", ".join(mentioned_labels) + "."
        else:
            summary = "No measurable observations were mentioned."
        return ExtractionOutput(
            observations=observations,
            not_mentioned=not_mentioned,
            summary=summary,
        )


def _compile_handlers() -> dict:
    """Return a mapping of ObservationType -> handler(text) -> obs | None."""

    def pain(text: str) -> ExtractedObservation | None:
        if not re.search(r"\bpain\b|\bach(e|es)?\b|\bsore\b", text):
            return None
        if re.search(r"\bno pain\b|\baching free\b", text):
            return ExtractedObservation(
                type=ObservationType.PAIN,
                value="0",
                unit="scale 0-10",
                confidence=0.9,
                note="Caregiver reported no pain.",
            )
        match = re.search(r"\b(\d{1,2})\s*(?:/10|out of ten|on a scale)", text)
        if match is None:
            match = re.search(r"\bpain\b[^.]{0,40}?\b(\d{1,2})\b", text)
        if match is None:
            match = re.search(r"\b(\d{1,2})\b[^.]{0,40}?\bpain\b", text)
        if match is not None:
            number = int(match.group(1))
            if 0 <= number <= 10:
                return ExtractedObservation(
                    type=ObservationType.PAIN,
                    value=str(number),
                    unit="scale 0-10",
                    confidence=0.9,
                    note="Pain level reported as a number.",
                )
        word_pattern = r"\b(?:pain(?:ful|ing)?|ache)\b[^.]{0,30}?\b(" + _number_words() + r")\b"
        word = re.search(word_pattern, text)
        if word is not None:
            return ExtractedObservation(
                type=ObservationType.PAIN,
                value=str(_NUMBERS[word.group(1)]),
                unit="scale 0-10",
                confidence=0.8,
                note="Pain level reported in words.",
            )
        return ExtractedObservation(
            type=ObservationType.PAIN,
            value=None,
            confidence=0.3,
            note="Pain mentioned but the level was not specified.",
        )

    def sleep(text: str) -> ExtractedObservation | None:
        if not re.search(r"\bsleep|slept|bed\b", text):
            return None
        num_token = r"(?:\d{1,2}|" + _number_words() + r")"
        match = re.search(rf"\bslept?\b[^.]{{0,40}}?({num_token})\s*(?:hours?|hrs?)?", text)
        if match is None:
            match = re.search(rf"({num_token})\s*(?:hours?|hrs?)\b[^.]{{0,40}}?\bsleep", text)
        if match is not None:
            raw = match.group(1)
            hours = int(raw) if raw.isdigit() else _NUMBERS.get(raw)
            if hours is not None:
                return ExtractedObservation(
                    type=ObservationType.SLEEP,
                    value=str(hours),
                    unit="hours",
                    confidence=0.9,
                    note="Sleep duration reported in hours.",
                )
        for word, note in (
            ("poorly", "Sleep was poor."),
            ("badly", "Sleep was poor."),
            ("restless", "Sleep was restless."),
            ("well", "Sleep was good."),
        ):
            if re.search(rf"\b{word}\b", text):
                return ExtractedObservation(
                    type=ObservationType.SLEEP,
                    value=word,
                    confidence=0.7,
                    note=note,
                )
        return ExtractedObservation(
            type=ObservationType.SLEEP,
            value=None,
            confidence=0.3,
            note="Sleep mentioned but no detail was given.",
        )

    def food_intake(text: str) -> ExtractedObservation | None:
        if not re.search(r"\beat\b|eats|food|appetite|meal(s)?", text):
            return None
        for word, note in [
            (("well",), "Ate well."),
            (("poorly", "little", "barely"), "Ate poorly."),
            (("no appetite", "not hungry"), "Reported no appetite."),
            (("no food", "not eating", "refusing"), "Reported not eating."),
            (("fine", "normally", "as usual"), "Eating as usual."),
        ]:
            if any(re.search(rf"\b{re.escape(token)}\b", text) for token in word):
                return ExtractedObservation(
                    type=ObservationType.FOOD_INTAKE,
                    value=word[0],
                    confidence=0.8,
                    note=note,
                )
        return ExtractedObservation(
            type=ObservationType.FOOD_INTAKE,
            value=None,
            confidence=0.3,
            note="Food intake mentioned without detail.",
        )

    def mobility(text: str) -> ExtractedObservation | None:
        if not re.search(r"\bwalk|mobil|moved|chair|bedridden|stood|up and about", text):
            return None
        for word, note in [
            (("up and about", "walking"), "Was up and about."),
            (("bedridden", "stayed in bed", "could not get up"), "Stayed in bed."),
            (("to the chair", "in the chair", "sat up"), "Sat up in a chair."),
        ]:
            if any(re.search(rf"\b{re.escape(token)}\b", text) for token in word):
                return ExtractedObservation(
                    type=ObservationType.MOBILITY,
                    value=word[0],
                    confidence=0.8,
                    note=note,
                )
        return ExtractedObservation(
            type=ObservationType.MOBILITY,
            value=None,
            confidence=0.3,
            note="Mobility mentioned without detail.",
        )

    def mood(text: str) -> ExtractedObservation | None:
        mapping = {
            "cheerful": ("Cheerful.", 0.8),
            "happy": ("Cheerful.", 0.8),
            "low": ("Mood reported as low.", 0.8),
            "down": ("Mood reported as low.", 0.7),
            "depressed": ("Mood reported as low.", 0.8),
            "anxious": ("Reported anxious.", 0.8),
            "anxiety": ("Reported anxious.", 0.8),
            "irritable": ("Reported irritable.", 0.8),
            "irritated": ("Reported irritable.", 0.8),
            "calm": ("Reported calm.", 0.8),
            "upset": ("Reported upset.", 0.8),
            "slept and seemed at peace": ("Seemed at peace.", 0.6),
        }
        for word, (note, confidence) in mapping.items():
            if re.search(rf"\b{re.escape(word)}\b", text):
                return ExtractedObservation(
                    type=ObservationType.MOOD,
                    value=word,
                    confidence=confidence,
                    note=note,
                )
        if re.search(r"\bmood\b", text):
            return ExtractedObservation(
                type=ObservationType.MOOD,
                value=None,
                confidence=0.3,
                note="Mood mentioned without detail.",
            )
        return None

    def breathing(text: str) -> ExtractedObservation | None:
        if not re.search(r"\bbreath|breathing|winded|dyspnoea|dyspnea", text):
            return None
        for word, note in [
            (("short of breath", "breathless", "winded"), "Short of breath."),
            (("comfortable", "fine", "ok", "normal", "easily"), "Breathing was comfortable."),
            (("laboured", "heavy"), "Breathing was laboured."),
        ]:
            if any(re.search(rf"\b{re.escape(token)}\b", text) for token in word):
                return ExtractedObservation(
                    type=ObservationType.BREATHING,
                    value=word[0],
                    confidence=0.8,
                    note=note,
                )
        return ExtractedObservation(
            type=ObservationType.BREATHING,
            value=None,
            confidence=0.3,
            note="Breathing mentioned without detail.",
        )

    def energy(text: str) -> ExtractedObservation | None:
        mapping = {
            "energetic": ("Seemed energetic.", 0.8),
            "lively": ("Seemed energetic.", 0.8),
            "tired": ("Seemed tired.", 0.8),
            "fatigued": ("Seemed fatigued.", 0.8),
            "exhausted": ("Seemed exhausted.", 0.8),
            "low energy": ("Reported low energy.", 0.8),
        }
        for word, (note, confidence) in mapping.items():
            if re.search(rf"\b{re.escape(word)}\b", text):
                return ExtractedObservation(
                    type=ObservationType.ENERGY,
                    value=word,
                    confidence=confidence,
                    note=note,
                )
        if re.search(r"\benergy\b", text):
            return ExtractedObservation(
                type=ObservationType.ENERGY,
                value=None,
                confidence=0.3,
                note="Energy mentioned without detail.",
            )
        return None

    return {
        ObservationType.PAIN: pain,
        ObservationType.SLEEP: sleep,
        ObservationType.FOOD_INTAKE: food_intake,
        ObservationType.MOBILITY: mobility,
        ObservationType.MOOD: mood,
        ObservationType.BREATHING: breathing,
        ObservationType.ENERGY: energy,
    }


def _number_words() -> str:
    return "|".join(_NUMBERS)


class OpenAIExtractionProvider:
    """LLM-backed provider.

    The ``openai`` package is imported lazily. Output is parsed and validated
    against ``ExtractionOutput``; anything that does not comply is rejected.
    """

    provider_name = "openai"
    model = ""

    def __init__(self, model: str, api_key: str) -> None:
        self.model = model
        self._api_key = api_key

    def extract(self, transcript: str, prompt_version: str) -> ExtractionOutput:
        try:
            import openai

            client = openai.OpenAI(api_key=self._api_key)
        except ImportError as exc:
            raise AIProviderError(
                "The OpenAI provider is configured but the 'openai' package is not installed."
            ) from exc

        try:
            response = client.chat.completions.create(
                model=self.model,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": transcript},
                ],
                response_format={"type": "json_object"},
            )
            content = (response.choices[0].message.content or "").strip()
        except Exception as exc:
            raise AppError(
                f"AI provider error: {exc}", code="AI_SERVICE_UNAVAILABLE", status_code=503
            ) from exc
        return _parse_provider_json(content)


def _parse_provider_json(content: str) -> ExtractionOutput:
    import json

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AIProviderError("AI provider returned invalid JSON") from exc
    try:
        return ExtractionOutput.model_validate(data)
    except Exception as exc:
        raise AIProviderError("AI provider output did not satisfy the extraction schema") from exc


def get_extraction_provider() -> AIProvider:
    settings = get_settings()
    if settings.ai_provider == "openai" and settings.openai_api_key:
        return OpenAIExtractionProvider(
            model=settings.openai_extraction_model, api_key=settings.openai_api_key
        )
    return LocalExtractionProvider()


def extract_from_transcript(
    transcript: str, provider: AIProvider | None = None
) -> ExtractionResult:
    """Extract candidate observations from ``transcript``.

    The transcript must already exist (it is never invented here); an empty
    transcript yields an empty extraction with a high not_mentioned list.
    """
    text = (transcript or "").strip()
    provider = provider or get_extraction_provider()
    prompt_version = get_settings().extraction_prompt_version or EXTRACTION_PROMPT_VERSION
    raw = provider.extract(text, prompt_version)

    # Final safety double-check mirroring the prompt rules: nothing with a
    # numeric value may enter unless it was explicitly stated with a number.
    for obs in raw.observations:
        if obs.value is not None and obs.value.isdigit():
            if obs.confidence < 0.5:
                obs.value = None

    confidence = _aggregate_confidence(raw)
    return ExtractionResult(
        output=raw,
        provider=provider.provider_name,
        model=provider.model,
        model_version=prompt_version,
        confidence=_clamp_confidence(confidence),
    )


def _aggregate_confidence(raw: ExtractionOutput) -> float | None:
    if not raw.observations:
        return None
    return sum(obs.confidence for obs in raw.observations) / len(raw.observations)
