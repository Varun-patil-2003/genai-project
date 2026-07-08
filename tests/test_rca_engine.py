import unittest
from unittest.mock import patch

from services.rca_engine import RCAEngine


class RCAEngineTest(unittest.TestCase):
    def test_gather_context_uses_ticket_info_key_and_log_excerpt(self):
        engine = RCAEngine()

        with patch(
            "services.rca_engine.rag_service.answer_question",
            return_value="Historical incidents with SDL poll response loss.",
        ):
            context = engine._gather_context(
                "1002",
                [
                    "73538900.001 |SdlError |SdlLinkHandler::sendPollRequest - Did not receive Poll Response From NodeId: 11, AppId: 100, TCPAddr[:0]",
                    "",
                ],
            )

        self.assertIn("ticket_info", context)
        self.assertNotIn("ticket-info", context)
        self.assertIn("Incident 1002", context["ticket_info"])
        self.assertIn("Did not receive Poll Response", context["log_excerpt"])
        self.assertIn("SDL_POLL_RESPONSE_MISSING", context["anomalies"])

    def test_generate_rca_text_formats_prompt_with_context(self):
        engine = RCAEngine()
        captured = {}

        class FakeCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)

                class Message:
                    content = "RCA text"

                class Choice:
                    message = Message()

                class Completion:
                    choices = [Choice()]

                return Completion()

        class FakeClient:
            class chat:
                completions = FakeCompletions()

        engine.client = FakeClient()

        text = engine._generate_rca_text(
            {
                "ticket_info": "Incident 1002",
                "anomalies": "SDL poll response missing",
                "historical_context": "Previous cluster link issue",
                "log_excerpt": "SdlLinkHandler::sendPollRequest - Did not receive Poll Response",
            }
        )

        self.assertEqual(text, "RCA text")
        prompt = captured["messages"][0]["content"]
        self.assertIn("Incident 1002", prompt)
        self.assertIn("SDL poll response missing", prompt)
        self.assertIn("Did not receive Poll Response", prompt)


if __name__ == "__main__":
    unittest.main()
