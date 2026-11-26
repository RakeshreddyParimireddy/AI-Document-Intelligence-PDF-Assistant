"""Split page text into small overlapping pieces ("chunks") for search.

Chunks never cross a page boundary, so every chunk has one exact page number
(needed later for citations like "invoice.pdf, page 2").
"""
from dataclasses import dataclass

from app.services.pdf_reader import PageText

CHUNK_SIZE = 800  # max characters per chunk
CHUNK_OVERLAP = 150  # characters repeated between neighbouring chunks, so no idea is cut in half


@dataclass
class ChunkText:
    page_number: int
    content: str


def split_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split one text into pieces of at most `size` characters, breaking between words."""
    text = " ".join(text.split())  # tidy up: collapse newlines and repeated spaces
    pieces: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # Break at the last space in the second half of the window, so we don't cut a word
            space = text.rfind(" ", start + size // 2, end)
            if space != -1:
                end = space

        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= len(text):
            break

        # Step back by `overlap` characters for the next chunk...
        start = max(end - overlap, start + 1)
        # ...and move forward to the start of a word
        if text[start - 1] != " ":
            next_space = text.find(" ", start, end)
            if next_space != -1:
                start = next_space + 1

    return pieces


def chunk_pages(pages: list[PageText]) -> list[ChunkText]:
    """Turn a PDF's pages into chunks, each remembering its page number."""
    return [
        ChunkText(page_number=page.page_number, content=piece)
        for page in pages
        for piece in split_text(page.text)
    ]
