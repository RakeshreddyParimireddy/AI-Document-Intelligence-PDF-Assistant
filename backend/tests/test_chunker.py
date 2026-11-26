"""Chunker tests: pure functions, no database needed."""
from app.services.chunker import CHUNK_OVERLAP, CHUNK_SIZE, chunk_pages, split_text
from app.services.pdf_reader import PageText

LONG_TEXT = " ".join(f"word{i}" for i in range(1000))  # about 7,800 characters


def test_short_text_is_one_chunk():
    assert split_text("Hello world") == ["Hello world"]


def test_empty_or_blank_text_gives_no_chunks():
    assert split_text("") == []
    assert split_text("   \n\t  ") == []


def test_chunks_are_not_longer_than_the_limit():
    chunks = split_text(LONG_TEXT)
    assert len(chunks) > 1
    assert all(len(chunk) <= CHUNK_SIZE for chunk in chunks)


def test_no_word_is_cut_in_half():
    for chunk in split_text(LONG_TEXT):
        for word in chunk.split():
            assert word.startswith("word") and word[4:].isdigit(), f"cut word: {word!r}"


def test_no_text_is_lost():
    words_in_chunks = {word for chunk in split_text(LONG_TEXT) for word in chunk.split()}
    assert words_in_chunks == set(LONG_TEXT.split())


def test_neighbouring_chunks_overlap():
    chunks = split_text(LONG_TEXT)
    for first, second in zip(chunks, chunks[1:]):
        # The start of each chunk repeats words from the end of the previous one
        first_word_of_second = second.split()[0]
        assert first_word_of_second in first.split()
        assert len(set(first.split()) & set(second.split())) * 6 >= CHUNK_OVERLAP // 2


def test_whitespace_is_tidied():
    assert split_text("Hello\n\n   world\t!") == ["Hello world !"]


def test_chunks_keep_their_page_number_and_skip_empty_pages():
    pages = [
        PageText(page_number=1, text="First page text."),
        PageText(page_number=2, text=""),  # e.g. an image-only page
        PageText(page_number=3, text=LONG_TEXT),
    ]
    chunks = chunk_pages(pages)
    assert chunks[0].page_number == 1 and chunks[0].content == "First page text."
    assert all(chunk.page_number == 3 for chunk in chunks[1:])
    assert len(chunks) > 2
    assert 2 not in {chunk.page_number for chunk in chunks}
