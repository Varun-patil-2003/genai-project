# "AI-Powered Incident Intelligence & Knowledge GenAI" || "NetOps AI Sentinel"

A system that:
1. Ingests logs, tickets, configs (like CUCM, SBC, or Call Managers and VoIP digital gateway)
2. Detects anomalies proactively
3. Suggests root cause + resolution
4. Auto-generates incident summaries + RCA reports
5. Acts as a chat-based assistant for L1/L2 engineers

Basically: Replace reactive support with predictive + AI-assisted operations


# Core Use Cases
1. Intelligent Ticket Analyzer
* Input: Zendesk/Jira tickets (historical + real-time)
* Output:
    * Category (network / SIP / hardware)
    * Priority
    * Probable root cause
    * Suggested fix

2. Log Anomaly Detection (ML + GenAI combo)
* Input: Logs
* Detect:
    * Pattern deviation
    * Error spikes
* Output:
    * “This looks like SIP registration failure due to X”

3. ChatOps Assistant (My UI module)
* Ask:
    * “Why is device not registering?”
    * “Show similar incidents last month”
* Output:
    * Context-aware answer using RAG

4. Auto RCA Generator
* Input: Incident data
* Output:
    * Structured RCA report:
        * Issue
        * Timeline
        * Root cause
        * Resolution
        * Prevention

5. Knowledge Base Builder (Self-learning system)
* Convert:
    * PDFs
    * Docs
    * Logs
* Into embeddings --> searchable intelligence



## Folder-to-responsibility mapping
- *api/* — All FastAPI route files. One file per domain: tickets.py, anomalies.py, chat.py, rca.py. Keep it thin — no business logic here, just routing to services.
- *app/* — App factory, middleware, config loader, startup/shutdown hooks. Your main.py lives here.
- *config/* — YAML/env config files. Separate configs for dev.yaml, prod.yaml. Never hardcode credentials.
- *data/* — Raw sample data for development. Subfolders: raw/ (original dumps), processed/ (cleaned CSVs), sample_tickets/, sample_logs/. This is your local test dataset.
- *embeddings/* — FAISS index files, embedding cache, and the embedding utility functions that call OpenAI's text-embedding-3-small.
- *eval/* — Evaluation scripts. Test your RAG quality, measure anomaly detection precision/recall, compare LLM responses. This is your quality gate before every release.
- *Logs/* — Application runtime logs. Use Python's logging module routed to structured JSON logs here.
- *models/* — Your ML model files: the trained XGBoost classifier .pkl files, Scikit-learn pipelines, and model versioning metadata.
- *pipelines/* — Data pipeline scripts. ingest_tickets.py, ingest_logs.py, embed_docs.py. These are the ETL jobs you run on schedule or trigger manually.
- *prompts/* — All LLM prompt templates as .txt or .jinja2 files. Never hardcode prompts inside Python code. Subfolders: rca/, summarization/, chat/. This makes iteration fast.
- *scripts/* — One-off utility scripts: seed_db.py, rebuild_index.py, export_rca.py. Not part of the main app, just developer tools.
- *services/* — Core business logic. ticket_service.py, log_service.py, rag_service.py, llm_service.py, anomaly_service.py. This is where the real intelligence lives.
- *tests/* — Unit and integration tests. Mirror the services/ structure: test_ticket_service.py, test_rag.py, etc.
- *ui/* — Phase 1: Streamlit app files. Phase 2: React app (you can create a ui/react/ subfolder when ready).
- *utils/* — Shared helpers: text_cleaner.py, log_parser.py, date_utils.py, chunk_splitter.py.



[Gemma 2](https://aistudio.google.com/prompts/1LrHk2-_QK002z_rPuKqeCsb1aCx_HSDx?utm_source=deepmind.google&utm_medium=referral&utm_campaign=gdm&utm_content=)
