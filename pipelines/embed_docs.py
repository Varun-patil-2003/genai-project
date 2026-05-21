import json
import os
from repository.vector_repo import vector_repo
from PyPDF2 import PdfReader
from utils.chunk_splitter import split_text

def ingest_tickets():
    with open('data/sample_tickets/tickets.json', 'r') as f:
        tickets = json.load(f)

    texts = []
    metadatas = []
    for t in tickets:
        content = f"Ticket {t['id']}: {t['title']}. Desc: {t['description']}. Resolution: {t['resolution_notes']}"
        texts.append(content)
        metadatas.append({"id": t['id'], "text": content, "source": "ticket"})
    
    vector_repo.add_documents(texts, metadatas)
    print("Tickets embedded successfully.")

def ingest_pdfs():
    pdf_folder = "data/raw/"
    all_texts = []
    all_metas = []

    for file in os.listdir(pdf_folder):
        if file.endswith('.pdf'):
            reader = PdfReader(os.path.join(pdf_folder, file))
            text = ""
            for page in reader.pages:
                text += page.extract_text()

            chunks = split_text(text, chunk_size=1000, overlap=100)
            for i, chunk in enumerate(chunks):
                all_texts.append(chunk)
                all_metas.append({'source': file, 'page': i, 'text': chunk})
        
        vector_repo.add_documents(all_texts, all_metas)
        print('PDFs embedded successfully.')

if __name__ == "__main__":
    ingest_tickets()
    ingest_pdfs()