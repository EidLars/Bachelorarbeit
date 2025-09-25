"""High-level orchestration of the greenwashing analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

from .claim_extraction import ClaimCandidate, ClaimExtractor
from .document_loader import PDFDocumentLoader
from .kpi_extraction import KPIExtractor, KPIRecord
from .llm_evaluator import ConsistencyEvaluator, EvaluationResult


@dataclass
class PipelineOutput:
    document_id: str
    claims: List[ClaimCandidate]
    kpis: List[KPIRecord]
    evaluations: List[EvaluationResult]

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "claims": [claim.__dict__ for claim in self.claims],
            "kpis": [kpi.to_dict() for kpi in self.kpis],
            "evaluations": [evaluation.to_dict() for evaluation in self.evaluations],
        }


class GreenwashingPipeline:
    """End-to-end pipeline for claim extraction, KPI parsing and consistency evaluation."""

    def __init__(
        self,
        claim_extractor: ClaimExtractor | None = None,
        kpi_extractor: KPIExtractor | None = None,
        evaluator: ConsistencyEvaluator | None = None,
        max_pages: int | None = None,
    ) -> None:
        self.document_loader = PDFDocumentLoader(max_pages=max_pages)
        self.claim_extractor = claim_extractor or ClaimExtractor()
        self.kpi_extractor = kpi_extractor or KPIExtractor()
        self.evaluator = evaluator

    def process(self, pdf_path: str | Path, evaluate: bool = True) -> PipelineOutput:
        sections = self.document_loader.load(pdf_path)
        claims = self.claim_extractor.extract_from_sections(sections)
        kpis = self.kpi_extractor.extract_from_sections(sections)
        evaluations: List[EvaluationResult] = []
        if evaluate and self.evaluator is not None:
            for claim in claims:
                evaluations.append(self.evaluator.evaluate(claim, kpis))
        return PipelineOutput(
            document_id=Path(pdf_path).stem,
            claims=claims,
            kpis=kpis,
            evaluations=evaluations,
        )

    def batch_process(self, pdf_paths: Sequence[str | Path], evaluate: bool = True) -> List[PipelineOutput]:
        outputs: List[PipelineOutput] = []
        for path in pdf_paths:
            outputs.append(self.process(path, evaluate=evaluate))
        return outputs

    def process_directory(self, directory: str | Path, evaluate: bool = True) -> List[PipelineOutput]:
        directory = Path(directory)
        pdf_paths = sorted(directory.glob("*.pdf"))
        return self.batch_process(pdf_paths, evaluate=evaluate)

