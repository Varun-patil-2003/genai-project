import argparse
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Generator

import faiss
import numpy as np
import pdfplumber
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

EMBEDDING_MODEL     = os.getenv("EMBEDDING_MODEL",     "all-MiniLM-L6-v2")
FAISS_INDEX_PATH    = Path(os.getenv("FAISS_INDEX_PATH",   "embeddings/faiss.index"))
FAISS_METADATA_PATH = Path(os.getenv("FAISS_METADATA_PATH","embeddings/metadata.json"))
DATA_RAW_PATH       = Path(os.getenv("DATA_RAW_PATH",      "data/raw"))
DATA_TICKETS_PATH   = Path(os.getenv("DATA_TICKETS_PATH",  "data/sample_tickets"))
CHUNK_SIZE          = int(os.getenv("RAG_CHUNK_SIZE",   "512"))
CHUNK_OVERLAP       = int(os.getenv("RAG_CHUNK_OVERLAP", "64"))

@dataclass
class Chunk:
    chunk_id:    str
    text:        str
    source_file: str
    source_type: str
    page_number: int
    ticket_id:   str
    timestamp:   str
    char_count:  int

def split_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    if not text or not text.strip():
        return []

    text = text.strip()
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap

    return chunks

def extract_pdf(pdf_path: Path) -> Generator[Chunk, None, None]:
    file_mtime = datetime.fromtimestamp(pdf_path.stat().st_mtime).isoformat()
    chunk_counter = 0
    skipped_pages = 0

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            log.info(f"  PDF: {pdf_path.name}  ({total_pages} pages)")

            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text(x_tolerance=3, y_tolerance=3)

                tables = page.extract_tables()
                if tables:
                    log.debug(
                        f"    Page {page_num}: {len(tables)} table(s) found "
                        f"— text included in chunks, raw table skipped"
                    )

                if not page_text or not page_text.strip():
                    skipped_pages += 1
                    log.warning(
                        f"    Page {page_num}: no text extracted "
                        f"(may be scanned/image — consider OCR)"
                    )
                    continue

                page_chunks = split_into_chunks(page_text)

                for chunk_text in page_chunks:
                    yield Chunk(
                        chunk_id    = f"{pdf_path.name}::chunk_{chunk_counter}",
                        text        = chunk_text,
                        source_file = pdf_path.name,
                        source_type = "pdf",
                        page_number = page_num,
                        ticket_id   = "",
                        timestamp   = file_mtime,
                        char_count  = len(chunk_text),
                    )
                    chunk_counter += 1

    except Exception as e:
        log.error(f"  Failed to process {pdf_path.name}: {e}")
        return

    if skipped_pages:
        log.warning(
            f"  {pdf_path.name}: {skipped_pages}/{total_pages} pages skipped "
            f"(no text layer). Run OCR on these pages for full coverage."
        )

    log.info(f"  → {chunk_counter} chunks from {pdf_path.name}")

def extract_ticket(ticket_path: Path) -> Generator[Chunk, None, None]:
    try:
        raw = json.loads(ticket_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        log.error(f"  Failed to parse {ticket_path.name}: {e}")
        return

    tickets = raw if isinstance(raw, list) else [raw]
    chunk_counter = 0

    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue

        ticket_id = str(ticket.get("id", ticket_path.stem))
        timestamp = ticket.get(
            "created_at",
            ticket.get("updated_at",
            datetime.fromtimestamp(ticket_path.stat().st_mtime).isoformat())
        )

        parts = []
        for field in ("title", "subject", "description", "body", "resolution", "solution", "notes"):
            value = ticket.get(field, "")
            if value and isinstance(value, str):
                parts.append(value.strip())

        if not parts:
            log.warning(f"  Ticket {ticket_id}: no usable text fields found — skipping")
            continue

        combined_text = "\n\n".join(parts)
        ticket_chunks = split_into_chunks(combined_text)

        for chunk_text in ticket_chunks:
            yield Chunk(
                chunk_id    = f"{ticket_path.name}::ticket_{ticket_id}::chunk_{chunk_counter}",
                text        = chunk_text,
                source_file = ticket_path.name,
                source_type = "ticket",
                page_number = 0,
                ticket_id   = ticket_id,
                timestamp   = str(timestamp),
                char_count  = len(chunk_text),
            )
            chunk_counter += 1

    log.info(f"  → {chunk_counter} chunks from {ticket_path.name}")

def embed_chunks(
    chunks: list[Chunk],
    model: SentenceTransformer,
    batch_size: int = 64,
) -> np.ndarray:
    texts = [c.text for c in chunks]
    log.info(f"Embedding {len(texts)} chunks (batch_size={batch_size})...")

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,   # cosine similarity via dot product on normalised vecs
        convert_to_numpy=True,
    )

    return embeddings.astype("float32")

def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    log.info(f"FAISS index built: {index.ntotal} vectors, dim={dim}")
    return index


def save_index(
    index: faiss.IndexFlatIP,
    metadata: list[dict],
    index_path: Path,
    metadata_path: Path,
) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(index_path))
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    index_size_mb = index_path.stat().st_size / 1024 / 1024
    log.info(f"Saved FAISS index → {index_path}  ({index_size_mb:.1f} MB)")
    log.info(f"Saved metadata    → {metadata_path}  ({len(metadata)} records)")


def load_index(
    index_path: Path,
    metadata_path: Path,
) -> tuple[faiss.IndexFlatIP, list[dict]]:
    index = faiss.read_index(str(index_path))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return index, metadata

def discover_sources() -> tuple[list[Path], list[Path]]:
    """Find all PDF and JSON files in the configured data directories."""
    pdfs = sorted(DATA_RAW_PATH.glob("**/*.pdf")) if DATA_RAW_PATH.exists() else []
    jsons = sorted(DATA_TICKETS_PATH.glob("**/*.json")) if DATA_TICKETS_PATH.exists() else []

    if not pdfs:
        log.warning(f"No PDFs found in {DATA_RAW_PATH} — add source PDFs to this folder")
    if not jsons:
        log.warning(f"No JSON tickets found in {DATA_TICKETS_PATH} — add ticket JSON files")

    log.info(f"Found {len(pdfs)} PDF(s) and {len(jsons)} JSON ticket file(s)")
    return pdfs, jsons

def run_rebuild() -> None:
    """Full rebuild: process all sources, overwrite existing index."""
    log.info("=" * 60)
    log.info("Mode: FULL REBUILD")
    log.info("=" * 60)
    start = time.time()

    pdfs, jsons = discover_sources()
    if not pdfs and not jsons:
        log.error("No source files found. Add PDFs to data/raw/ and tickets to data/sample_tickets/")
        sys.exit(1)

    all_chunks: list[Chunk] = []

    log.info("\n── Extracting PDFs ──────────────────────────────────────")
    for pdf_path in tqdm(pdfs, desc="PDFs", unit="file"):
        all_chunks.extend(extract_pdf(pdf_path))

    log.info("\n── Extracting JSON tickets ──────────────────────────────")
    for json_path in tqdm(jsons, desc="Tickets", unit="file"):
        all_chunks.extend(extract_ticket(json_path))

    if not all_chunks:
        log.error("No chunks extracted. Check your source files.")
        sys.exit(1)

    log.info(f"\nTotal chunks: {len(all_chunks)}")
    avg_chars = sum(c.char_count for c in all_chunks) / len(all_chunks)
    log.info(f"Average chunk size: {avg_chars:.0f} characters")

    log.info(f"\n── Loading embedding model: {EMBEDDING_MODEL} ──────────")
    model = SentenceTransformer(EMBEDDING_MODEL)

    log.info("\n── Embedding ────────────────────────────────────────────")
    embeddings = embed_chunks(all_chunks, model)

    log.info("\n── Building FAISS index ─────────────────────────────────")
    index = build_faiss_index(embeddings)

    log.info("\n── Saving ───────────────────────────────────────────────")
    metadata = [asdict(c) for c in all_chunks]
    save_index(index, metadata, FAISS_INDEX_PATH, FAISS_METADATA_PATH)

    elapsed = time.time() - start
    log.info(f"\n✓ Rebuild complete in {elapsed:.1f}s")
    log.info(f"  {len(all_chunks)} chunks indexed from {len(pdfs)} PDFs + {len(jsons)} ticket files")


def run_incremental() -> None:
    log.info("=" * 60)
    log.info("Mode: INCREMENTAL UPDATE")
    log.info("=" * 60)

    if not FAISS_INDEX_PATH.exists() or not FAISS_METADATA_PATH.exists():
        log.warning("No existing index found — running full rebuild instead")
        run_rebuild()
        return

    index, metadata = load_index(FAISS_INDEX_PATH, FAISS_METADATA_PATH)
    existing_files = {m["source_file"] for m in metadata}
    log.info(f"Existing index: {index.ntotal} vectors from {len(existing_files)} source files")

    pdfs, jsons = discover_sources()

    new_pdfs  = [p for p in pdfs  if p.name not in existing_files]
    new_jsons = [j for j in jsons if j.name not in existing_files]

    if not new_pdfs and not new_jsons:
        log.info("No new files found. Index is up to date.")
        return

    log.info(f"New files: {len(new_pdfs)} PDF(s), {len(new_jsons)} JSON ticket file(s)")

    new_chunks: list[Chunk] = []
    for pdf_path in new_pdfs:
        new_chunks.extend(extract_pdf(pdf_path))
    for json_path in new_jsons:
        new_chunks.extend(extract_ticket(json_path))

    if not new_chunks:
        log.warning("New files found but no chunks extracted.")
        return

    model = SentenceTransformer(EMBEDDING_MODEL)
    new_embeddings = embed_chunks(new_chunks, model)
    index.add(new_embeddings)

    updated_metadata = metadata + [asdict(c) for c in new_chunks]
    save_index(index, updated_metadata, FAISS_INDEX_PATH, FAISS_METADATA_PATH)

    log.info(f"✓ Added {len(new_chunks)} new chunks. Index total: {index.ntotal}")


def run_stats() -> None:
    if not FAISS_INDEX_PATH.exists():
        log.error(f"No index found at {FAISS_INDEX_PATH}. Run --rebuild first.")
        sys.exit(1)

    index, metadata = load_index(FAISS_INDEX_PATH, FAISS_METADATA_PATH)

    source_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {"pdf": 0, "ticket": 0}

    for m in metadata:
        src = m["source_file"]
        source_counts[src] = source_counts.get(src, 0) + 1
        type_counts[m["source_type"]] = type_counts.get(m["source_type"], 0) + 1

    print("\n" + "=" * 60)
    print("FAISS Index Stats")
    print("=" * 60)
    print(f"Total vectors : {index.ntotal}")
    print(f"Embedding dim : {index.d}")
    print(f"PDF chunks    : {type_counts.get('pdf', 0)}")
    print(f"Ticket chunks : {type_counts.get('ticket', 0)}")
    print(f"\nSource files ({len(source_counts)} total):")
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        print(f"  {count:>5} chunks  {src}")
    print("=" * 60)

def run_test_query(query: str) -> None:
    if not FAISS_INDEX_PATH.exists():
        log.error("No index found. Run --rebuild first.")
        sys.exit(1)

    log.info(f'Test query: "{query}"')

    index, metadata = load_index(FAISS_INDEX_PATH, FAISS_METADATA_PATH)
    model = SentenceTransformer(EMBEDDING_MODEL)

    query_vec = model.encode([query], normalize_embeddings=True).astype("float32")
    distances, indices = index.search(query_vec, k=5)

    print(f'\nTop 5 results for: "{query}"\n')
    for rank, (dist, idx) in enumerate(zip(distances[0], indices[0]), start=1):
        if idx == -1:
            continue
        m = metadata[idx]
        preview = m["text"][:200].replace("\n", " ")
        print(f"  [{rank}] score={dist:.4f}  source={m['source_file']}  type={m['source_type']}")
        if m["source_type"] == "ticket":
            print(f"       ticket_id={m['ticket_id']}")
        if m["source_type"] == "pdf":
            print(f"       page={m['page_number']}")
        print(f"       \"{preview}...\"")
        print()

def main() -> None:
    parser = argparse.ArgumentParser(
        description="NetOps AI Sentinel — data ingestion & embedding pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipelines/embed_docs.py --rebuild
  python pipelines/embed_docs.py --incremental
  python pipelines/embed_docs.py --stats
  python pipelines/embed_docs.py --query "Registration Timeout on London SBC"
        """,
    )
    parser.add_argument("--rebuild",     action="store_true", help="Full rebuild of the index")
    parser.add_argument("--incremental", action="store_true", help="Add only new files to the index")
    parser.add_argument("--stats",       action="store_true", help="Show index statistics")
    parser.add_argument("--query",       type=str,            help="Run a test retrieval query")

    args = parser.parse_args()

    if args.rebuild:
        run_rebuild()
    elif args.incremental:
        run_incremental()
    elif args.stats:
        run_stats()
    elif args.query:
        run_test_query(args.query)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()