from typing import Dict, List, Any
from groq import Groq
import os
from dotenv import load_dotenv

from config.constants import RCAConfig
from core.exceptions import LLMInferenceError, RCAGenetionError
from services.rag_service import rag_service
from utils.pdf_generator import RCAPDFGenerator
from services.anomaly_service import anomaly_service

load_dotenv()

class RCAEngine:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.pdf_gen = RCAPDFGenerator()

    def _gather_context(self, ticket_id: str, logs: List[str]) -> Dict[str, Any]:
        ticket_info = f"Incident {ticket_id}: High priority connectivity failure in London Hub."

        anomalies = anomaly_service.scan_logs(logs)
        anomaly_summary = str(anomalies)

        historical_context = rag_service.answer_question(f"Past incidents similar to {ticket_info}")

        return {
            "ticket-info": ticket_info,
            "anomalies": anomaly_summary,
            "historical_context": historical_context
        }
    
    def _generate_rca_text(self, context: Dict[str, Any]) -> str:
        prompt = RCAConfig.RCA_PROMPT_TEMPLATE.format(
            ticket_info=context['ticket_info'],
            anomalies=context['anomalies'],
            historical_context=context['historical_context']
        )

        try:
            completion = self.client.chat.completions.create(
                model=RCAConfig.MODEL_NAME,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=RCAConfig.TEMPERATURE
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise LLMInferenceError(f"Groq API failed to generate RCA: {str(e)}")
    
    def produce_final_report(self, ticket_id: str, logs: List[str]) -> str:
        """
        Main entry point to generate a professional RCA PDF.
        
        Args:
            ticket_id (str): The ID of the incident.
            logs (List[str]): The raw log lines associated with the incident.
            
        Returns:
            str: Path to the final PDF report.
        """
        try:
            context = self._gather_context(ticket_id, logs)

            rca_text = self._generate_rca_text(context)

            pdf_path = self.pdf_gen.generate(ticket_id, rca_text)

            return pdf_path
        
        except (LLMInferenceError, Exception) as e:
            raise RCAGenetionError(f"Critical failure in RCA pipeline: {str(e)}")
        
rca_engine = RCAEngine()
