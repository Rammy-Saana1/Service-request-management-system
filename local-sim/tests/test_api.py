import json
import tempfile
import threading
import unittest
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen

from app import create_server


class ApiTests(unittest.TestCase):
    MANAGER_PASSCODE = "correct-horse-battery-staple"

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "api-test.db"
        self.server = create_server(
            "127.0.0.1",
            0,
            database_path,
            self.MANAGER_PASSCODE,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp_dir.cleanup()

    def call(self, path, method="GET", payload=None, *, raw_body=None, headers=None):
        body = raw_body if raw_body is not None else (
            None if payload is None else json.dumps(payload).encode("utf-8")
        )
        request_headers = dict(headers or {})
        if payload is not None and "Content-Type" not in request_headers:
            request_headers["Content-Type"] = "application/json"
        request = Request(
            self.base_url + path,
            data=body,
            method=method,
            headers=request_headers,
        )
        try:
            with self.opener.open(request, timeout=3) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            return error.code, json.loads(error.read())

    def login(self, reviewer="Local Manager", passcode=None):
        return self.call(
            "/api/manager/login",
            "POST",
            {
                "reviewer": reviewer,
                "passcode": passcode or self.MANAGER_PASSCODE,
            },
        )

    def test_health_and_static_page(self):
        status, payload = self.call("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload, {"status": "ok", "mode": "simulated"})
        with urlopen(self.base_url + "/", timeout=3) as response:
            html = response.read().decode("utf-8")
            self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("Service Request Management", html)

    def test_complete_api_workflow(self):
        status, created = self.call(
            "/api/requests",
            "POST",
            {
                "title": "Outlook will not open",
                "description": "Outlook closes immediately after I start it on my test laptop.",
                "requester": "Taylor Reed",
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(created["category"], "Microsoft 365")

        self.assertEqual(self.login()[0], 200)
        status, queue = self.call("/api/requests?status=Awaiting%20review")
        self.assertEqual(status, 200)
        self.assertEqual([item["id"] for item in queue["items"]], [created["id"]])

        status, approved = self.call(
            f"/api/requests/{created['id']}/decision",
            "POST",
            {
                "decision": "approve",
                "reviewed_by": "Local Manager",
                "review_comment": "Proposal checked.",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(approved["status"], "Approved")
        self.assertEqual(approved["reviewed_by"], "Local Manager")

        status, error = self.call(
            f"/api/requests/{created['id']}/decision",
            "POST",
            {"decision": "reject", "reviewed_by": "Other Manager", "review_comment": "Late"},
        )
        self.assertEqual(status, 409)
        self.assertIn("already been reviewed", error["error"])

    def test_api_rejects_invalid_request(self):
        status, payload = self.call(
            "/api/requests",
            "POST",
            {"title": "", "description": "", "requester": ""},
        )
        self.assertEqual(status, 400)
        self.assertIn("required", payload["error"])

    def test_manager_routes_require_authentication(self):
        status, created = self.call(
            "/api/requests",
            "POST",
            {
                "title": "Test printer failure",
                "description": "The test printer fails whenever a document is submitted.",
                "requester": "Employee",
            },
        )
        self.assertEqual(status, 201)

        self.assertEqual(self.call("/api/requests")[0], 401)
        self.assertEqual(self.call(f"/api/requests/{created['id']}")[0], 401)
        status, error = self.call(
            f"/api/requests/{created['id']}/decision",
            "POST",
            {"decision": "approve", "reviewed_by": "Impersonated Manager"},
        )
        self.assertEqual(status, 401)
        self.assertIn("sign-in", error["error"])

        self.assertEqual(self.login("Verified Manager")[0], 200)
        status, request = self.call(f"/api/requests/{created['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(request["status"], "Awaiting review")

    def test_manager_identity_comes_from_session_and_logout_revokes_access(self):
        self.assertEqual(self.login("Verified Manager")[0], 200)
        status, created = self.call(
            "/api/requests",
            "POST",
            {
                "title": "Test access request",
                "description": "A test employee needs access for a future training exercise.",
                "requester": "Employee",
            },
        )
        self.assertEqual(status, 201)
        status, approved = self.call(
            f"/api/requests/{created['id']}/decision",
            "POST",
            {
                "decision": "approve",
                "reviewed_by": "Spoofed Name",
                "review_comment": "Checked locally.",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(approved["reviewed_by"], "Verified Manager")

        self.assertEqual(self.call("/api/manager/logout", "POST")[0], 200)
        self.assertEqual(self.call("/api/requests")[0], 401)

    def test_invalid_manager_credentials_are_rejected(self):
        status, payload = self.login(passcode="wrong-passcode-value")
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "Invalid manager credentials.")
        self.assertEqual(self.call("/api/manager/session")[0], 401)

    def test_api_rejects_wrong_content_type_and_invalid_utf8(self):
        status, payload = self.call(
            "/api/requests",
            "POST",
            raw_body=b"title=test",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status, 400)
        self.assertIn("application/json", payload["error"])

        status, payload = self.call(
            "/api/requests",
            "POST",
            raw_body=b"\xff\xfe",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(status, 400)
        self.assertIn("UTF-8 JSON", payload["error"])

    def test_server_rejects_non_loopback_binding(self):
        with self.assertRaisesRegex(ValueError, "loopback"):
            create_server(
                "0.0.0.0",
                0,
                Path(self.temp_dir.name) / "unsafe.db",
                self.MANAGER_PASSCODE,
            )


if __name__ == "__main__":
    unittest.main()
