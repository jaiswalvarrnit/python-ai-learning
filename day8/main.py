
from pathlib import Path
from pypdf import PdfReader

from chunking import (
    fixed_size_chunking,
    recursive_chunking,
    heading_based_chunking
)


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(pdf_path)
    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)

    return "\n\n".join(pages)


def load_all_pdfs(folder: str) -> dict:
    documents = {}

    for pdf_path in Path(folder).glob("*.pdf"):
        documents[pdf_path.name] = extract_pdf_text(pdf_path)

    return documents


def compare_chunking(documents):

    strategies = {
        "Fixed": fixed_size_chunking,
        "Recursive": recursive_chunking,
        "Heading": heading_based_chunking
    }

    for filename, text in documents.items():

        print("\n" + "=" * 70)
        print(f"DOCUMENT: {filename}")
        print("=" * 70)

        for strategy_name, strategy in strategies.items():

            chunks = strategy(text)

            avg_size = (
                sum(len(chunk) for chunk in chunks) / len(chunks)
                if chunks else 0
            )

            print(f"\nStrategy: {strategy_name}")
            print(f"Number of chunks: {len(chunks)}")
            print(f"Average chunk size: {avg_size:.2f} characters")

            for index, chunk in enumerate(chunks[:2]):
                print(f"\nChunk {index + 1}:")
                print(chunk[:200])


if __name__ == "__main__":

    documents = load_all_pdfs("day8_sample_pdfs")

    print(f"Total PDFs loaded: {len(documents)}")

    compare_chunking(documents)
