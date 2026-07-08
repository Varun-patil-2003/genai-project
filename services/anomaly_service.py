import re
import json
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
            "AUTH_FORBIDDEN": r"403 Forbidden",
            "SDL_POLL_RESPONSE_MISSING": r"Did not receive Poll Response From NodeId:\s*\d+"
        }
        self.anomaly_terms = re.compile(
            r"\b(error|critical|fail(?:ed|ure)?|exception|timeout|timed out|refused|"
            r"denied|forbidden|unreachable|down|reset|abort|disconnect|no response|"
            r"not receive|not received|lost|degraded|unavailable)\b",
            re.IGNORECASE,
        )
    
    def scan_logs(self, log_lines: list) -> list:
        anomalies = []
        for line in log_lines:
            clean_line = line.strip()
            if not clean_line:
                continue

            matched_signature = False
            for label, pattern in self.signatures.items():
                if re.search(pattern, clean_line):
                    anomalies.append({"type": "SIGNATURE", "label": label, "line": clean_line})
                    matched_signature = True

            if not matched_signature and self._looks_anomalous(clean_line):
                anomalies.append({
                    "type": "AI_CANDIDATE",
                    "label": self._classify_candidate(clean_line),
                    "line": clean_line
                })

        error_count = sum(1 for line in log_lines if "ERROR" in line.upper() or "CRITICAL" in line.upper())
        if error_count > 10:
            anomalies.append({"type": "STATISTICAL", "label": "ERROR_SPIKE", "line": f"Detected {error_count} errors in window"})
        
        return anomalies

    def enrich_anomalies(self, anomalies: list, max_ai_findings: int = 12) -> list:
        if not anomalies:
            return []

        for item in anomalies:
            item["ai_insight"] = self._fallback_insight(item)

        if not os.getenv("GROQ_API_KEY") or not os.getenv("MODEL_NAME"):
            return anomalies

        prompt = self._build_batch_prompt(anomalies[:max_ai_findings])
        try:
            completion = client.chat.completions.create(
                model=os.getenv("MODEL_NAME"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                timeout=12
            )
            insights = self._parse_insights(completion.choices[0].message.content)
            for index, insight in insights.items():
                if 0 <= index < len(anomalies) and insight:
                    anomalies[index]["ai_insight"] = insight
        except Exception:
            pass

        return anomalies

    def explain_anomaly(self, anomaly_detail: str, label: str = None) -> str:
        prompt = f"As a NetOps expert, explain the root cause and potential impact of this log anomaly: {anomaly_detail}. Keep it concise and technical."
        try:
            completion = client.chat.completions.create(
                model=os.getenv("MODEL_NAME"),
                messages=[{
                    "role": 'user',
                    "content": prompt
                }],
                temperature=0.1,
                timeout=8
            )
            return completion.choices[0].message.content
        except Exception:
            return "Detected by log pattern. Review the affected component, timestamp sequence, and adjacent error lines for root cause."

    def _looks_anomalous(self, line: str) -> bool:
        return bool(self.anomaly_terms.search(line))

    def _classify_candidate(self, line: str) -> str:
        upper_line = line.upper()
        if "TIMEOUT" in upper_line or "TIMED OUT" in upper_line:
            return "TIMEOUT_OR_LATENCY"
        if "AUTH" in upper_line or "FORBIDDEN" in upper_line or "DENIED" in upper_line:
            return "AUTH_OR_ACCESS_FAILURE"
        if "UNREACHABLE" in upper_line or "NO RESPONSE" in upper_line or "NOT RECEIVE" in upper_line:
            return "REACHABILITY_FAILURE"
        if "FAIL" in upper_line or "ERROR" in upper_line or "CRITICAL" in upper_line:
            return "ERROR_EVENT"
        return "ANOMALOUS_LOG_EVENT"

    def _build_batch_prompt(self, anomalies: list) -> str:
        findings = []
        for index, item in enumerate(anomalies):
            findings.append(
                f"{index}. type={item.get('type')} label={item.get('label')} "
                f"count={item.get('count', 1)} line={item.get('line')}"
            )

        return (
            "You are a senior NetOps/telecom incident analyst. Analyze these log anomalies. "
            "For each item, infer the likely technical meaning, impact, and first checks. "
            "Return only compact JSON where keys are the numeric indexes as strings and values "
            "are concise one-sentence insights. Do not include markdown.\n\n"
            + "\n".join(findings)
        )

    def _parse_insights(self, content: str) -> dict:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            return {}

        parsed = json.loads(match.group(0))
        return {int(key): str(value) for key, value in parsed.items()}

    def _fallback_insight(self, item: dict) -> str:
        label = item.get("label", "ANOMALOUS_LOG_EVENT")
        line = item.get("line", "")
        if label == "SDL_POLL_RESPONSE_MISSING":
            return "CUCM SDL link polling is not receiving peer responses; check node reachability, SDL link state, service health, and inter-node packet loss."
        if label == "SIP_503":
            return "The SIP peer is rejecting service; check trunk reachability, upstream overload, route patterns, and SIP service health."
        if label == "ERROR_SPIKE":
            return "The log window contains an abnormal error volume; identify the first error in the sequence and correlate with service or network changes."
        if "timeout" in line.lower() or "timed out" in line.lower():
            return "The event indicates latency or no response from a dependency; check reachability, packet loss, firewall policy, and target service health."
        if "denied" in line.lower() or "forbidden" in line.lower():
            return "The event indicates an access or authorization failure; verify credentials, roles, token validity, and source restrictions."
        return "This line contains failure language outside known signatures; review adjacent logs, affected component state, and recent changes to confirm root cause."
    
anomaly_service = AnomalyService()
