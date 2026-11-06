import tempfile
import unittest
from pathlib import Path

from database import Database
from service import ConflictError, RequestService, ValidationError
from simulated_ai import classify


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        self.service = RequestService(Database(self.database_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_request(self, **overrides):
        payload = {
            "title": "VPN outage for the office",
            "description": "All users in the entire office cannot connect to the VPN this morning.",
            "requester": "Alex Morgan",
        }
        payload.update(overrides)
        return self.service.create(payload)

    def test_create_classifies_and_persists_for_review(self):
        created = self.create_request()
        self.assertEqual(created["category"], "Network")
        self.assertEqual(created["priority"], "Critical")
        self.assertEqual(created["status"], "Awaiting review")
        self.assertEqual(created["ai_mode"], "simulated")
        self.assertEqual(self.service.get(created["id"])["title"], created["title"])

    def test_manager_can_edit_and_approve(self):
        created = self.create_request()
        approved = self.service.decide(
            created["id"],
            {
                "decision": "approve",
                "reviewed_by": "Jordan Manager",
                "review_comment": "Impact confirmed with the support lead.",
                "category": "Network",
                "priority": "High",
                "ai_summary": "Office VPN connectivity is unavailable for the test group.",
                "suggested_reply": "Thanks for the report. The service desk is investigating the VPN issue.",
            },
        )
        self.assertEqual(approved["status"], "Approved")
        self.assertEqual(approved["priority"], "High")
        self.assertEqual(approved["reviewed_by"], "Jordan Manager")
        self.assertIsNotNone(approved["reviewed_at"])

    def test_manager_can_reject_with_reason(self):
        created = self.create_request()
        rejected = self.service.decide(
            created["id"],
            {
                "decision": "reject",
                "reviewed_by": "Jordan Manager",
                "review_comment": "Duplicate of request 17.",
            },
        )
        self.assertEqual(rejected["status"], "Rejected")
        self.assertEqual(rejected["review_comment"], "Duplicate of request 17.")

    def test_rejection_requires_reason(self):
        created = self.create_request()
        with self.assertRaisesRegex(ValidationError, "reason is required"):
            self.service.decide(
                created["id"],
                {"decision": "reject", "reviewed_by": "Manager", "review_comment": ""},
            )

    def test_request_cannot_be_reviewed_twice(self):
        created = self.create_request()
        payload = {
            "decision": "approve",
            "reviewed_by": "Manager",
            "review_comment": "Checked.",
        }
        self.service.decide(created["id"], payload)
        with self.assertRaises(ConflictError):
            self.service.decide(created["id"], payload)

    def test_form_validation_rejects_short_description(self):
        with self.assertRaisesRegex(ValidationError, "at least 20"):
            self.create_request(description="Too short")
        self.assertEqual(self.service.list(), [])

    def test_form_validation_rejects_non_text_values(self):
        with self.assertRaisesRegex(ValidationError, "Title must be text"):
            self.create_request(title={"unexpected": "object"})
        self.assertEqual(self.service.list(), [])

    def test_review_validation_rejects_non_text_values(self):
        created = self.create_request()
        with self.assertRaisesRegex(ValidationError, "Review Comment must be text"):
            self.service.decide(
                created["id"],
                {
                    "decision": "approve",
                    "reviewed_by": "Manager",
                    "review_comment": ["not", "text"],
                },
            )
        self.assertEqual(self.service.get(created["id"])["status"], "Awaiting review")

    def test_rule_engine_uses_low_priority_for_how_to_request(self):
        result = classify(
            "How do I install the reporting application?",
            "I would like instructions when possible; this is not blocking my work.",
        )
        self.assertEqual(result["category"], "Software")
        self.assertEqual(result["priority"], "Low")


if __name__ == "__main__":
    unittest.main()
