"""Greenwashing detection toolkit built on ClimateBERT and DeepSeek R1 Zero."""

from .claim_extraction import ClaimCandidate, ClaimExtractor
from .document_loader import DocumentSection, PDFDocumentLoader, iter_pdf_directory, consolidate_sections
from .kpi_extraction import KPIExtractor, KPIRecord
from .llm_evaluator import ConsistencyEvaluator, EvaluationResult
from .pipeline import GreenwashingPipeline, PipelineOutput

__all__ = [
    "ClaimCandidate",
    "ClaimExtractor",
    "DocumentSection",
    "PDFDocumentLoader",
    "iter_pdf_directory",
    "consolidate_sections",
    "KPIExtractor",
    "KPIRecord",
    "ConsistencyEvaluator",
    "EvaluationResult",
    "GreenwashingPipeline",
    "PipelineOutput",
]

