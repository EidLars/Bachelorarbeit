"""Utilities for loading documents that feed the greenwashing pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List

import pdfplumber


@dataclass
class DocumentSection:
    """Represents a chunk of text taken from a document."""

    document_id: str
    page_number: int
    text: str


class PDFDocumentLoader:
    """Light-weight PDF loader that extracts page texts."""

    def __init__(self, max_pages: int | None = None) -> None:
        self.max_pages = max_pages

    def load(self, path: str | Path) -> List[DocumentSection]:
        pdf_path = Path(path)
        sections: List[DocumentSection] = []
        with pdfplumber.open(pdf_path) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                if self.max_pages is not None and idx > self.max_pages:
                    break
                text = page.extract_text() or ""
                normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
                sections.append(
                    DocumentSection(
                        document_id=pdf_path.stem,
                        page_number=idx,
                        text=normalized,
                    )
                )
        return sections


def iter_pdf_directory(directory: str | Path, max_pages: int | None = None) -> Iterator[DocumentSection]:
    """Yield sections for every PDF in a directory."""

    loader = PDFDocumentLoader(max_pages=max_pages)
    directory = Path(directory)
    for pdf_path in sorted(directory.glob("*.pdf")):
        yield from loader.load(pdf_path)


def consolidate_sections(sections: Iterable[DocumentSection]) -> str:
    """Join multiple sections back into a single text blob."""

    return "\n\n".join(section.text for section in sections if section.text)

