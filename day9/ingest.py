
import re
from pathlib import Path

from pypdf import PdfReader
from psycopg.types.json import Jsonb

from db import get_connection
from embeddings import generate_embedding


PDF_FOLDER = Path(__file__).resolve().parent / "day8_sample_pdfs"
CHUNK_SIZE = 500
OVERLAP = 50


def fixed_chunks(text: str) -> list[str]:

    chunks = []
    start = 0

    while start < len(text):

        end = start + CHUNK_SIZE

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += CHUNK_SIZE - OVERLAP

    return chunks


def find_section(text: str, chunk_start: int) -> str:

    pattern = r"(?m)^\s*\d+\.\s+[^\n]+"

    headings = list(re.finditer(pattern, text[:chunk_start + 1]))

    if not headings:
        return "Introduction"

    return headings[-1].group().strip()


def ingest_pdf(pdf_path: Path):

    reader = PdfReader(pdf_path)

    with get_connection() as conn:

        with conn.cursor() as cur:

            for page_number, page in enumerate(reader.pages, start=1):

                text = page.extract_text() or ""

                chunks = fixed_chunks(text)

                for chunk in chunks:

                    # Find where this chunk begins in the page text.
                    chunk_start = text.find(chunk)

                    section = find_section(
                        text,
                        max(chunk_start, 0)
                    )

                    embedding = generate_embedding(chunk)

                    metadata = {
                        "file_type": "pdf",
                        "chunking_strategy": "fixed",
                        "chunk_size": CHUNK_SIZE,
                        "overlap": OVERLAP
                    }

                    cur.execute(
                        """
                        INSERT INTO document_chunks
                        (content, embedding, metadata, source, page, section)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (source, page, content) DO NOTHING
                        """,
                        (
                            chunk,
                            embedding,
                            Jsonb(metadata),
                            pdf_path.name,
                            page_number,
                            section
                        )
                    )

        conn.commit()


def main():

    pdf_files = list(PDF_FOLDER.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF files")

    for pdf_path in pdf_files:

        print(f"\nIngesting: {pdf_path.name}")

        ingest_pdf(pdf_path)

        print("Completed:", pdf_path.name)

    print("\nAll documents processed!")


if __name__ == "__main__":
    main()
