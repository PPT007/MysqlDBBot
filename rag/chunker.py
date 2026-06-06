from pathlib import Path
from typing import List, Optional

DEFAULT_SCHEMA_PATH = Path("docs/schema.txt")


def load_schema(schema_path: Optional[Path] = None) -> str:
    """Load schema text from a file path."""
    path = Path(schema_path or DEFAULT_SCHEMA_PATH)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    return path.read_text(encoding="utf-8").strip()


def parse_schema_sections(schema_text: str) -> List[str]:
    """Split schema text into logical sections for chunking."""
    lines = [line.rstrip() for line in schema_text.splitlines()]
    sections: List[str] = []
    current: List[str] = []

    def add_current() -> None:
        if current:
            text = "\n".join(current).strip()
            if text:
                sections.append(text)
            current.clear()

    for line in lines:
        if line.startswith("Table:") or line.startswith("========== RELATIONSHIPS"):
            add_current()
            current.append(line)
        else:
            current.append(line)

    add_current()
    return sections


def _split_long_section(section: str, chunk_size: int, overlap: int) -> List[str]:
    """Split a single section into smaller chunks if it exceeds the chunk size."""
    lines = section.splitlines()
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1
        if current_len + line_len > chunk_size and current:
            chunks.append("\n".join(current).strip())
            if overlap > 0:
                current = current[-overlap:]
                current_len = sum(len(item) + 1 for item in current)
            else:
                current = []
                current_len = 0

        current.append(line)
        current_len += line_len

    if current:
        chunks.append("\n".join(current).strip())

    return chunks


def chunk_schema_text(
    schema_text: str,
    chunk_size: int = 600,
    overlap: int = 1,
) -> List[str]:
    """Create chunks from schema text with one chunk per table/section.
    
    Each table and the relationships section become separate chunks.
    Large sections are split internally if they exceed chunk_size.
    """
    sections = parse_schema_sections(schema_text)
    chunks: List[str] = []

    for section in sections:
        section_len = len(section)

        if section_len > chunk_size:
            # Split large sections internally, but keep them separate.
            chunks.extend(_split_long_section(section, chunk_size, overlap))
        else:
            # Keep each small section as its own chunk.
            chunks.append(section)

    return [chunk for chunk in chunks if chunk]


def create_schema_chunks(
    schema_path: Optional[Path] = None,
    chunk_size: int = 600,
    overlap: int = 1,
) -> List[str]:
    """Load the schema file and return a list of text chunks."""
    schema_text = load_schema(schema_path)
    return chunk_schema_text(schema_text, chunk_size=chunk_size, overlap=overlap)


def write_chunks(
    chunks: List[str],
    output_dir: Optional[Path] = None,
    prefix: str = "schema_chunk",
) -> Path:
    """Write chunks to numbered text files in a directory."""
    directory = Path(output_dir or Path("rag") / "chunks")
    directory.mkdir(parents=True, exist_ok=True)

    for index, chunk in enumerate(chunks, start=1):
        file_path = directory / f"{prefix}_{index}.txt"
        file_path.write_text(chunk, encoding="utf-8")

    return directory


if __name__ == "__main__":
    chunks = create_schema_chunks()
    print(f"Created {len(chunks)} schema chunks\n")
    for index, chunk in enumerate(chunks, start=1):
        print(f"--- Chunk {index} ---\n{chunk}\n")
