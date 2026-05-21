def split_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list:
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        chunk = text[start:end]
        chunks.append(chunk)

        start += (chunk_size - overlap)

        if start >= text_length or chunk_size <= overlap:
            break

        return chunks