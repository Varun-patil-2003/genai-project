import re
# import pandas as pd
# from sklearn.ensemble import IsolationForest
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class AnomalyService:
    def __init__(self):
        self.signatures = {
            "SIP_503": r"SIP/2.0 503 Service Unavailable",
            "DB_SYNC_FAIL": r"Database synchronization failure",
            "SOCKET_TIMEOUT": r"Socket timeout on port \d+",
            "AUTH_FORBIDDEN": r"403 Forbidden"
        }
    
    def scan_logs(self, log_lines: list) -> list:
        anomalies = []
        for line in log_lines:
            for label, pattern in self.signatures.items():
                if re.search(pattern, line):
                    anomalies.append({"type": "SIGNATURE", "label": label, "line": line})

        error_count = sum(1 for line in log_lines if "ERROR" in line or "CRITICAL" in line)
        if error_count > 10:
            anomalies.append({"type": "STATISTICAL", "label": "ERROR_SPIKE", "line": f"Detected {error_count} errors in window"})
        
        return anomalies

    def explain_anomaly(self, anomaly_detail: str) -> str:
        prompt = f"As a NetOps expert, explain the root cause and potential impact of this log anomaly: {anomaly_detail}. Keep it concise and technical."
        completion = client.chat.completions.create(
            model=os.getenv("MODEL_NAME"),
            messages=[{
                "role": 'user',
                "content": prompt
            }],
            temperature=0.1
        )
        return completion.choices[0].message.content
    
anomaly_service = AnomalyService()