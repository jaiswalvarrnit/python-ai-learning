def fixed_size_chunking(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> list[str]:

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between 0 and chunk_size")

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end]
        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks

import re


def recursive_chunking(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> list[str]:

    separators = ["\n\n", "\n", ". ", " "]

    def split_text(text: str) -> list[str]:

        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        for separator in separators:

            parts = text.split(separator)

            if len(parts) <= 1:
                continue

            chunks = []
            current = ""

            for part in parts:
                candidate = (
                    current + separator + part
                    if current else part
                )

                if len(candidate) <= chunk_size:
                    current = candidate
                else:
                    if current:
                        chunks.extend(split_text(current))

                    current = part

            if current:
                chunks.extend(split_text(current))

            return chunks

        # Fallback: split an unusually long unbroken segment.
        return [
            text[i:i + chunk_size]
            for i in range(0, len(text), chunk_size)
        ]

    chunks = split_text(text)

    # Add overlap between consecutive chunks.
    if overlap == 0:
        return chunks

    result = []

    for i, chunk in enumerate(chunks):
        if i > 0:
            previous = chunks[i - 1]
            chunk = previous[-overlap:] + chunk

        result.append(chunk)

    return result

def heading_based_chunking(text: str) -> list[str]:

    heading_pattern = r"(?m)^\s*\d+\.\s+[A-Z][^\n]*$"

    sections = re.split(
        heading_pattern,
        text
    )

    headings = re.findall(
        heading_pattern,
        text
    )

    chunks = []

    for index, section in enumerate(sections):

        section = section.strip()

        if not section:
            continue

        if index == 0:
            chunks.append(section)
        else:
            heading = headings[index - 1]
            chunks.append(heading + "\n" + section)

    return chunks