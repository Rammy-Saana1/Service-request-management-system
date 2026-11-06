import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import Database


VALID_REQUEST = {
    "title": "Printer needs maintenance",
    "description": "The printer leaves a test streak on every page but still operates.",
    "requester": "Test Employee",
    "category": "Hardware",
    "priority": "Medium",
    "summary": "Printer needs maintenance: The printer leaves a test streak.",
    "suggested_reply": "Thanks for the report. An agent will review the printer details.",
}


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "database-test.db"
        self.database = Database(self.path)
        self.database.initialize()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_request_persists_after_database_is_reopened(self):
        created = self.database.create_request(VALID_REQUEST)
        reopened = Database(self.path)
        reopened.initialize()
        self.assertEqual(reopened.get_request(created["id"])["title"], created["title"])

    def test_database_rejects_invalid_category_even_when_service_is_bypassed(self):
        invalid = {**VALID_REQUEST, "category": "Invented category"}
        with self.assertRaisesRegex(sqlite3.IntegrityError, "integrity check"):
            self.database.create_request(invalid)
        self.assertEqual(self.database.list_requests(), [])

    def test_database_rejects_final_status_without_review_metadata(self):
        created = self.database.create_request(VALID_REQUEST)
        connection = sqlite3.connect(self.path)
        try:
            with self.assertRaisesRegex(sqlite3.IntegrityError, "integrity check"):
                connection.execute(
                    "UPDATE service_requests SET status = 'Approved' WHERE id = ?",
                    (created["id"],),
                )
        finally:
            connection.close()
        self.assertEqual(self.database.get_request(created["id"])["status"], "Awaiting review")


if __name__ == "__main__":
    unittest.main()
