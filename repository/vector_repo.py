import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import pickle
from typing import List, Tuple
import faiss
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings


class VectorRepository:

    def __init__(
        self,
        index_path="embeddings/faiss_index.bin",
        metadata_path="embeddings/metadata.pkl",
    ):
        self.index_path = index_path
        self.metadata_path = metadata_path

        # Fixed: Using the free local HuggingFace embeddings instead of OpenAI
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        self.index = None
        self.metadata = []
        self._load_index()

    def _load_index(self):
        # Ensure the directory exists so saving doesn't crash later
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)

        if os.path.exists(self.index_path) and os.path.exists(
            self.metadata_path
        ):
            print("Loading existing FAISS index...")
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, "rb") as f:
                self.metadata = pickle.load(f)
        else:
            print("No existing index found. Starting fresh.")

    def add_documents(self, texts: List[str], metadatas: List[dict]):
        embeddings_list = self.embeddings.embed_documents(texts)
        embeddings_array = np.array(embeddings_list).astype("float32")

        if self.index is None:
            dimension = embeddings_array.shape[1]
            self.index = faiss.IndexFlatL2(dimension)

        self.index.add(embeddings_array)

        # Map texts inside metadata dictionaries for the search recovery
        for text, meta in zip(texts, metadatas):
            meta_copy = meta.copy()
            meta_copy["text"] = text
            self.metadata.append(meta_copy)

        self.save()

    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)
        print("Index saved successfully!")

    def search(self, query: str, k=3) -> List[Tuple[str, dict]]:
        if self.index is None:
            print("Index is empty!")
            return []

        query_vec = np.array([self.embeddings.embed_query(query)]).astype(
            "float32"
        )
        distances, indices = self.index.search(query_vec, k)

        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.metadata):
                results.append((self.metadata[idx]["text"], self.metadata[idx]))
        return results
vector_repo = VectorRepository()

if __name__ == "__main__":  # Test code to verify it works
    test_texts = [
        "React is a frontend framework for UI development.",
        "Node.js runs JavaScript on the server side.",
        "FAISS is an efficient library for dense vector similarity search.",
    ]     # Sample documents to test indexing
    test_metadata = [{"source": "web"}, {"source": "backend"}, {"source": "ai"}]

    print("\nAdding test documents...")
    vector_repo.add_documents(test_texts, test_metadata)

    print("\nTesting search query...")
    query = "How to build a web user interface?"
    matched_results = vector_repo.search(query, k=1)

    for text, meta in matched_results:
        print(f"Match Found: {text} | Metadata: {meta}")