import asyncio
import unittest
from unittest.mock import patch

from api.anomalies import LogRequest, scan_logs
from services.anomaly_service import AnomalyService


class AnomalyServiceTest(unittest.TestCase):
    def test_known_sdl_poll_error_gets_local_insight(self):
        service = AnomalyService()
        anomalies = [{
            "type": "SIGNATURE",
            "label": "SDL_POLL_RESPONSE_MISSING",
            "line": "SdlLinkHandler::sendPollRequest - Did not receive Poll Response From NodeId: 11",
            "count": 1
        }]

        with patch.dict("os.environ", {}, clear=True):
            insight = service.enrich_anomalies(anomalies)[0]["ai_insight"]

        self.assertIn("SDL link polling", insight)

    def test_scan_endpoint_deduplicates_repeated_anomalies(self):
        logs = [
            "SdlLinkHandler::sendPollRequest - Did not receive Poll Response From NodeId: 11",
            "SdlLinkHandler::sendPollRequest - Did not receive Poll Response From NodeId: 11",
        ]

        with patch("api.anomalies.anomaly_service.enrich_anomalies") as enrich:
            enrich.side_effect = lambda anomalies: anomalies
            response = asyncio.run(scan_logs(LogRequest(logs=logs)))

        self.assertEqual(response["status"], "completed")
        self.assertEqual(len(response["anomalies"]), 1)
        self.assertEqual(response["anomalies"][0]["count"], 2)
        enrich.assert_called_once()

    def test_unknown_failure_line_is_detected_as_ai_candidate(self):
        service = AnomalyService()
        anomalies = service.scan_logs([
            "2026-07-08 10:15:01 ComponentX failed to acquire session lock after retry budget exhausted"
        ])

        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["type"], "AI_CANDIDATE")
        self.assertEqual(anomalies[0]["label"], "ERROR_EVENT")

    def test_batch_enrichment_uses_ai_response_when_available(self):
        service = AnomalyService()
        anomalies = [{
            "type": "AI_CANDIDATE",
            "label": "ERROR_EVENT",
            "line": "ComponentX failed to acquire session lock",
            "count": 1
        }]

        class FakeCompletions:
            def create(self, **kwargs):
                class Message:
                    content = '{"0":"AI says the component is blocked on session lock contention."}'

                class Choice:
                    message = Message()

                class Completion:
                    choices = [Choice()]

                return Completion()

        class FakeClient:
            class chat:
                completions = FakeCompletions()

        with patch.dict("os.environ", {"GROQ_API_KEY": "test", "MODEL_NAME": "test-model"}):
            with patch("services.anomaly_service.client", FakeClient()):
                enriched = service.enrich_anomalies(anomalies)

        self.assertEqual(
            enriched[0]["ai_insight"],
            "AI says the component is blocked on session lock contention."
        )


if __name__ == "__main__":
    unittest.main()
