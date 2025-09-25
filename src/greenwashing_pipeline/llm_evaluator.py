"""Consistency evaluation powered by DeepSeek R1 Zero via OpenRouter."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Iterable, List, Optional

import requests

from .claim_extraction import ClaimCandidate
from .config import MODELS, OPENROUTER
from .kpi_extraction import KPIRecord


@dataclass
class EvaluationResult:
    """Structured output for the alignment check."""

    claim: ClaimCandidate
    kpis: List[KPIRecord]
    consistency: str
    greenwashing_signal: str
    confidence: Optional[float]
    explanation: str
    evidence_refs: List[str]
    raw_response: dict

    def to_dict(self) -> dict:
        return {
            "claim": {
                "text": self.claim.text,
                "label": self.claim.label,
                "score": self.claim.score,
                "document_id": self.claim.document_id,
                "page_number": self.claim.page_number,
            },
            "kpis": [kpi.to_dict() for kpi in self.kpis],
            "consistency": self.consistency,
            "greenwashing_signal": self.greenwashing_signal,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "evidence_refs": self.evidence_refs,
            "raw_response": self.raw_response,
        }


class ConsistencyEvaluator:
    """Wrapper around the DeepSeek R1 Zero API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        api_base: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or os.getenv(OPENROUTER.api_key_env)
        self.model_name = model_name or MODELS.deepseek_model
        self.api_base = api_base or OPENROUTER.api_base

    def evaluate(self, claim: ClaimCandidate, kpis: Iterable[KPIRecord]) -> EvaluationResult:
        if not self.api_key:
            raise RuntimeError(
                "No OpenRouter API key provided. Set the OPENROUTER_API_KEY environment variable "
                "before calling the evaluator."
            )

        kpi_list = list(kpis)
        payload = {
            "model": self.model_name,
            "response_format": {"type": "json_object"},
            "messages": _build_messages(claim, kpi_list),
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            self.api_base,
            headers=headers,
            json=payload,
            timeout=OPENROUTER.request_timeout,
        )
        response.raise_for_status()
        data = response.json()
        raw_message = data["choices"][0]["message"]["content"]
        parsed = _safe_parse_json(raw_message)

        return EvaluationResult(
            claim=claim,
            kpis=kpi_list,
            consistency=parsed.get("consistency", "unknown"),
            greenwashing_signal=parsed.get("greenwashing_signal", "unknown"),
            confidence=_coerce_float(parsed.get("confidence")),
            explanation=parsed.get("explanation", ""),
            evidence_refs=parsed.get("evidence_refs", []),
            raw_response=data,
        )


def _build_messages(claim: ClaimCandidate, kpis: List[KPIRecord]) -> List[dict]:
    kpi_table = _format_kpis(kpis)
    user_prompt = (
        "You are a sustainability analyst. Review the claim and the numerical evidence and respond "
        "with a JSON object containing the fields: consistency (one of consistent, contradiction, "
        "unclear), greenwashing_signal (low, medium, high), confidence (0-1 float), explanation "
        "(max 3 sentences) and evidence_refs (list of KPI identifiers)."
    )
    task_description = (
        "Claim under review:\n"
        f"{claim.text}\n\n"
        "Detected KPIs:\n"
        f"{kpi_table}\n"
        "Mark evidence_refs with the KPI type and page, e.g. scope_emissions@12."
    )
    return [
        {"role": "system", "content": user_prompt},
        {"role": "user", "content": task_description},
    ]


def _format_kpis(kpis: List[KPIRecord]) -> str:
    if not kpis:
        return "No KPIs available."
    rows = ["| KPI | Value | Unit | Year | Page |", "| --- | --- | --- | --- | --- |"]
    for kpi in kpis:
        identifier = kpi.metadata.get("scope", kpi.kpi_type)
        rows.append(
            f"| {identifier} | {kpi.value:.2f} | {kpi.unit or '-'} | {kpi.year or '-'} | {kpi.page_number} |"
        )
    return "\n".join(rows)


def _safe_parse_json(raw_message: str) -> dict:
    try:
        return json.loads(raw_message)
    except json.JSONDecodeError:
        return {}


def _coerce_float(value) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

