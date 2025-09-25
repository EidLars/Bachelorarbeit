"""Configuration constants for the greenwashing detection pipeline."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    """Configuration bundle for machine learning models."""

    climatebert_model: str = "climatebert/distilroberta-base-climate-fever"
    deepseek_model: str = "deepseek/deepseek-r1-zero"


@dataclass(frozen=True)
class ExtractionConfig:
    """Parameters that steer the extraction heuristics."""

    claim_score_threshold: float = 0.55
    supported_claim_labels: tuple[str, ...] = ("SUPPORTS", "REFUTES")
    contradiction_labels: tuple[str, ...] = ("REFUTES", "CONTRADICTION")
    text_chunk_size: int = 6  # number of sentences merged before inference to keep context


@dataclass(frozen=True)
class OpenRouterConfig:
    """Defaults for talking to the OpenRouter API."""

    api_base: str = "https://openrouter.ai/api/v1/chat/completions"
    api_key_env: str = "OPENROUTER_API_KEY"
    request_timeout: int = 60


MODELS = ModelConfig()
EXTRACTION = ExtractionConfig()
OPENROUTER = OpenRouterConfig()

