"""Heuristic extraction of sustainability KPIs from text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from .document_loader import DocumentSection


@dataclass
class KPIRecord:
    """Structured KPI instance."""

    kpi_type: str
    value: float
    unit: Optional[str]
    year: Optional[int]
    source_text: str
    document_id: str
    page_number: int
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "kpi_type": self.kpi_type,
            "value": self.value,
            "unit": self.unit,
            "year": self.year,
            "document_id": self.document_id,
            "page_number": self.page_number,
            "metadata": self.metadata,
            "source_text": self.source_text,
        }


class KPIExtractor:
    """Naive regex-based KPI extraction tailored to emission reporting."""

    SCOPE_PATTERN = re.compile(
        r"(?P<label>Scope\s*(?P<scope>[123]|total))[^\d]*(?P<value>\d[\d\.,]*)\s*(?P<unit>Mt|kt|t|tonnes?|tCO2e?|CO2e?)",
        re.IGNORECASE,
    )
    TOTAL_EMISSIONS_PATTERN = re.compile(
        r"(?P<label>(?:total|overall)\s+emissions)[^\d]*(?P<value>\d[\d\.,]*)\s*(?P<unit>Mt|kt|t|tonnes?|tCO2e?|CO2e?)",
        re.IGNORECASE,
    )
    REDUCTION_PATTERN = re.compile(
        r"(?P<label>reduc(?:ed|tion))[^\d%]*(?P<value>\d{1,3}(?:[\.,]\d+)?)\s*%[^\d]{0,40}?(?P<year>20\d{2})?",
        re.IGNORECASE,
    )
    RENEWABLE_PATTERN = re.compile(
        r"(?P<label>renewable(?:\s+energy)?)\W+(?P<value>\d{1,3}(?:[\.,]\d+)?)\s*%",
        re.IGNORECASE,
    )
    YEAR_PATTERN = re.compile(r"(20\d{2})")

    def extract_from_sections(self, sections: Iterable[DocumentSection]) -> List[KPIRecord]:
        records: List[KPIRecord] = []
        for section in sections:
            records.extend(self._extract_from_section(section))
        return records

    def _extract_from_section(self, section: DocumentSection) -> List[KPIRecord]:
        matches: List[KPIRecord] = []
        for pattern, kpi_type in [
            (self.SCOPE_PATTERN, "scope_emissions"),
            (self.TOTAL_EMISSIONS_PATTERN, "total_emissions"),
        ]:
            for match in pattern.finditer(section.text):
                value = _parse_number(match.group("value"))
                if value is None:
                    continue
                unit = match.group("unit")
                scope = match.groupdict().get("scope")
                metadata = {}
                if scope:
                    metadata["scope"] = scope.lower()
                year = _infer_year(section.text, match.start(), match.end())
                matches.append(
                    KPIRecord(
                        kpi_type=kpi_type,
                        value=value,
                        unit=unit,
                        year=year,
                        source_text=_extract_context(section.text, match.start(), match.end()),
                        document_id=section.document_id,
                        page_number=section.page_number,
                        metadata=metadata,
                    )
                )

        for match in self.REDUCTION_PATTERN.finditer(section.text):
            value = _parse_number(match.group("value"))
            if value is None:
                continue
            year = match.group("year")
            matches.append(
                KPIRecord(
                    kpi_type="emission_reduction_percent",
                    value=value,
                    unit="%",
                    year=int(year) if year else _infer_year(section.text, match.start(), match.end()),
                    source_text=_extract_context(section.text, match.start(), match.end()),
                    document_id=section.document_id,
                    page_number=section.page_number,
                    metadata={},
                )
            )

        for match in self.RENEWABLE_PATTERN.finditer(section.text):
            value = _parse_number(match.group("value"))
            if value is None:
                continue
            matches.append(
                KPIRecord(
                    kpi_type="renewable_energy_share",
                    value=value,
                    unit="%",
                    year=_infer_year(section.text, match.start(), match.end()),
                    source_text=_extract_context(section.text, match.start(), match.end()),
                    document_id=section.document_id,
                    page_number=section.page_number,
                    metadata={},
                )
            )

        return matches


def _parse_number(raw: str | None) -> Optional[float]:
    if not raw:
        return None
    normalized = raw.replace(".", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def _infer_year(text: str, start: int, end: int, window: int = 40) -> Optional[int]:
    snippet = text[max(0, start - window) : min(len(text), end + window)]
    match = KPIExtractor.YEAR_PATTERN.search(snippet)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _extract_context(text: str, start: int, end: int, padding: int = 80) -> str:
    return text[max(0, start - padding) : min(len(text), end + padding)].strip()

