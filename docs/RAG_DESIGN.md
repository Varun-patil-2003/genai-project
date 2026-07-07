# RAG Design — Module B: Knowledge Brain

This document captures the design decisions for the RAG pipeline so every contributor starts with the same mental model.

---

## Data sources

| Source | Format | Location | Content |
|---|---|---|---|
| Telecom runbooks | PDF | `data/raw/` | SBC configs, CUCM procedures, TPO docs |
| Historical tickets | JSON | `data/sample_tickets/` | Zendesk/Jira exports |

---

## Ingestion pipeline (`pipelines/embed_docs.py`)

### Step 1 — Extract text

- PDFs → `pdfplumber` (layout-aware; handles tables in SBC config docs)
- JSON tickets → stdlib `json` parser, concatenate relevant fields: `title + description + resolution`

### Step 2 — Chunk

- Strategy: fixed-size with overlap
- `RAG_CHUNK_SIZE=512` characters
- `RAG_CHUNK_OVERLAP=64` characters
- Each chunk stores metadata: `{source_file, page_number, ticket_id, timestamp}`

### Step 3 — Embed

- Model: `all-MiniLM-L6-v2` via `sentence-transformers`
- Why: fast, runs locally, no API cost, good performance on technical text
- Embeddings are 384-dimensional float32 vectors

### Step 4 — Index

- Store: `faiss-cpu` with `IndexFlatL2`
- Index file: `embeddings/faiss.index`
- Metadata (chunk text + source) stored separately: `embeddings/metadata.json`
- Rebuild by running: `python pipelines/embed_docs.py --rebuild`

---

## Retrieval (`services/rag_service.py`)

1. Embed the user query with the same `all-MiniLM-L6-v2` model
2. FAISS `search(query_vector, k=RAG_TOP_K)` → top-5 chunks by L2 distance
3. Rerank: sort by recency if `ticket_timestamp` metadata is present (recent incidents score higher)
4. Return chunks as context to the LLM

---

## Chat prompt structure (`prompts/chat/rag_chat.jinja2`)

```
System: You are a NetOps assistant for L1/L2 engineers...
Context:
{% for chunk in retrieved_chunks %}
[Source: {{ chunk.source }}]
{{ chunk.text }}
{% endfor %}

User question: {{ user_query }}
```

---

## Evaluation (`eval/rag_eval.py`)

Metrics to track on every rebuild:
- **Hit rate**: does the correct source appear in the top-5 results?
- **MRR** (Mean Reciprocal Rank): how high does the correct source rank?
- **Answer faithfulness**: does the LLM answer stay grounded in the retrieved context?

Run: `python eval/rag_eval.py --sample eval/golden_questions.json`

---

## Known limitations

- FAISS `IndexFlatL2` does exact search — fine for datasets up to ~100k chunks. Switch to `IndexIVFFlat` if index grows beyond that.
- No re-ranker model currently. If retrieval quality degrades, add a cross-encoder reranker (e.g. `cross-encoder/ms-marco-MiniLM-L-6-v2`).
- PDF tables from SBC config exports are partially extracted — complex nested tables may lose structure. Log warnings in `pipelines/embed_docs.py` for pages where table extraction fails.