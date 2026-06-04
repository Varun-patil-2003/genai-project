from fastapi import APIRouter
from services.anomaly_service import anomaly_service
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix='/anomalies', tags=['Anomaly Detection'])

class LogRequest(BaseModel):
    logs: List[str]

@router.post("/scan")
async def scan_logs(request: LogRequest):
    detected = anomaly_service.scan_logs(request.logs)

    results = []
    for item in detected:
        explanation = anomaly_service.explain_anomaly(item['line'])
        results.append({**item, "ai_insight": explanation})

    return {'status': "completed", "anomalies": results}