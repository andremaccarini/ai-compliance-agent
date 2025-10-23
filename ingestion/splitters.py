from typing import List

def split_text(text: str, max_chars: int = 1200, overlap: int = 150) -> List[str]:

    """
    Split a long text into overlapping chunks for embedding/indexing.

    Args:
        text:       full text string to split.
        max_chars:  maximum number of characters per chunk (default = 1200).
        overlap:    number of characters overlapped between consecutive chunks
                    to preserve sentence continuity (default = 150).

    Returns:
        List[str]: list of text chunks.

    Notes:
        - Used during ingestion to prepare document segments for FAISS indexing.
        - Overlap ensures context is not lost at chunk boundaries.
        - Character-based splitting is lightweight and language-agnostic.
    """

    chunks = []
    start = 0
    n = len(text)

    # Slide window over text to create overlapping chunks
    while start < n:
        end = min(start + max_chars, n)
        chunk = text[start:end]
        if start != 0:
            chunk = text[max(0, start-overlap):end]
        chunks.append(chunk)
        start += max_chars
    return chunks
