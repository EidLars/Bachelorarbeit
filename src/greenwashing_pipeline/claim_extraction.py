"""Claim extraction powered by ClimateBERT."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

from .config import EXTRACTION, MODELS
from .document_loader import DocumentSection


_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


@dataclass
class ClaimCandidate:
    """Structured representation of a potential environmental claim."""

    text: str
    label: str
    score: float
    document_id: str
    page_number: int

    @property
    def is_contradiction(self) -> bool:
        return self.label.upper() in {label.upper() for label in EXTRACTION.contradiction_labels}


class ClaimExtractor:
    """Identifies potential green claims using ClimateBERT."""

    def __init__(
        self,
        model_name: str | None = None,
        score_threshold: float | None = None,
        claim_labels: Sequence[str] | None = None,
    ) -> None:
        model_name = model_name or MODELS.climatebert_model
        score_threshold = score_threshold or EXTRACTION.claim_score_threshold
        claim_labels = claim_labels or EXTRACTION.supported_claim_labels

        self.score_threshold = score_threshold
        self.claim_labels = tuple(label.upper() for label in claim_labels)

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self._classifier = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            return_all_scores=True,
            truncation=True,
        )

    def extract_from_sections(self, sections: Iterable[DocumentSection]) -> List[ClaimCandidate]:
        claims: List[ClaimCandidate] = []
        for section in sections:
            claims.extend(self._extract_from_section(section))
        return claims

    def _extract_from_section(self, section: DocumentSection) -> List[ClaimCandidate]:
        candidates: List[ClaimCandidate] = []
        for sentence in _split_sentences(section.text):
            prediction = self._classifier(sentence)
            if not prediction:
                continue
            label_scores = {entry["label"].upper(): entry["score"] for entry in prediction[0]}
            for claim_label in self.claim_labels:
                score = label_scores.get(claim_label)
                if score and score >= self.score_threshold:
                    candidates.append(
                        ClaimCandidate(
                            text=sentence.strip(),
                            label=claim_label,
                            score=score,
                            document_id=section.document_id,
                            page_number=section.page_number,
                        )
                    )
                    break
        return candidates


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences while keeping numeric content intact."""

    raw_sentences = _SENTENCE_BOUNDARY.split(text)
    sentences = [sentence.strip() for sentence in raw_sentences if sentence.strip()]
    return sentences

