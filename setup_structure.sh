#!/usr/bin/env bash
# ============================================================
# NetOps AI Sentinel — Project Structure Setup
# Run this once after cloning:  bash setup_structure.sh
# Creates missing folders mentioned in README that don't
# exist yet in the repo tree.
# ============================================================

set -e

FOLDERS=(
  "prompts/rca"
  "prompts/classifier"
  "prompts/chat"
  "prompts/summarization"
  "scripts"
  "ui"
  "logs"
  "reports"
  "data/raw"
  "data/processed"
  "data/sample_tickets"
  "data/sample_logs"
  "docs"
  "tests/integration"
)

echo "Creating project folder structure..."

for folder in "${FOLDERS[@]}"; do
  if [ ! -d "$folder" ]; then
    mkdir -p "$folder"
    touch "$folder/.gitkeep"
    echo "  created: $folder/"
  else
    echo "  exists:  $folder/"
  fi
done

echo ""
echo "Done. Next steps:"
echo "  1. cp env.example .env"
echo "  2. Fill in .env with your API keys"
echo "  3. pip install -r requirements.txt"
echo "  4. python pipelines/embed_docs.py --rebuild"
