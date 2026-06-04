from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class RCAConfig:
    MODEL_NAME: str = os.getenv("MODEL_NAME")
    TEMPERATURE: float = 0.1

    RCA_PROMPT_TEMPLATE = """
    You are a Senior Network Architect. Generate a formal Root Cause Analysis (RCA) report.

    INPUT DATA:
    - Ticket Details: {ticket_info}
    - Log Anomalies: {anomalies}
    - Historical Context: {historical_context}

    The report MUST follow this professional structure:
    1. EXECUTIVE SUMMARY: High-level overview of the outage.
    2. INCIDENT TIMELINE: Sequence of events leading to failure.
    3. TECHNICAL ROOT CAUSE: Deep dive into why the failure occurred.
    4. RESOLUTION STEPS: Exactly how the issue was fixed.
    5. PREVENTATIVE MEASURES: Long-term architectural changes to prevent recurrence.
    
    Tone: Formal, Technical, Objective.
    """