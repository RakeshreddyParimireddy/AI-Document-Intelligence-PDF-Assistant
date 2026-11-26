"""Read text out of a PDF, one page at a time (uses PyMuPDF)."""
from dataclasses import dataclass

import pymupdf


@dataclass
class PageText:
    page_number: int  # starts at 1, like a PDF viewer
    text: str


def extract_pages(pdf_path: str) -> list[PageText]:
    """Return the text of every page. Raises an error if the file is not a readable PDF."""
    pages = []
    with pymupdf.open(pdf_path) as doc:
        for index, page in enumerate(doc):
            pages.append(PageText(page_number=index + 1, text=page.get_text().strip()))
    return pages
