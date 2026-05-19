from repository.vector_repo import vector_repo
# from openai import OpenAI
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class RAGServices:
    def __init__(self):
        self.system_prompt = """
        You're the NetOps AI Sentinal, an expert in Cisco CUCM and SBC systems.
        Use the provided context to answer the engineer's question.
        If the answer is not in the context, say "I cannot find a historical record of this issue,"
        but suggest a general troubleshooting step based on network principles.
        """
    
    def answer_question(self, query: str) -> str:
        # 1. Retrieve relevent context
        context_docs = vector_repo.search(query, k=3)
        context_text = "\n\n".join([doc[0] for doc in context_docs])

        # 2. Build the prompt
        user_message = f"Context:\n{context_text}\n\nQuestion: {query}"

        # 3. Call LLM
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content

rag_service = RAGServices()

if __name__ == "__main__":
    print("\n--- Testing RAG System ---")
    
    test_query = "How do I resolve a registration issue on Cisco CUCM?"
    
    print(f"User Query: {test_query}")
    print("Generating AI Response...")
    
    ai_response = rag_service.answer_question(test_query)
    print("\nAI Response:")
    print(ai_response)
