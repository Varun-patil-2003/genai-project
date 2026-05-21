from fastapi import APIRouter
from services.rag_service import rag_service
from pydantic import BaseModel

router = APIRouter(prefix='/chat', tags=['AI Assistant'])

class QueryRequest(BaseModel):
    query: str

@router.post('/ask')
async def ask_ai(request: QueryRequest):
    answer = rag_service.answer_question(request.query)
    return {"answer": answer}