from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.rca_engine import rca_engine
from core.exceptions import RCAGenetionError

router = APIRouter(prefix="/rca", tags=['RCA Generation'])

class RCARequest(BaseModel):
    ticket_id: str
    logs: List[str]

@router.post("/generate")

async def generate_rca(request: RCARequest):
    try:
        pdf_path = rca_engine.produce_final_report(request.ticket_id, request.logs)
        return {
            "status": "success",
            "message": "RCA Report generated successfully",
            "path": pdf_path
        }
    except RCAGenetionError as e:
        raise HTTPException(status_code=500, detail=str(e))