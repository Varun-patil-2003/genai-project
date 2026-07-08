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
    seen = {}
    for item in detected:
        key = (item["type"], item["label"], item["line"])
        if key in seen:
            seen[key]["count"] += 1
            continue

        result = {**item, "count": 1}
        seen[key] = result
        results.append(result)

    results = anomaly_service.enrich_anomalies(results)

    return {'status': "completed", "anomalies": results}
