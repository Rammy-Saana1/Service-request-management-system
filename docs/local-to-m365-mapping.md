# Local prototype to Microsoft 365 mapping

| Local component | Microsoft 365 equivalent | What differs |
|---|---|---|
| `local-sim/web/index.html`, `app.js`, and `styles.css` intake form | Power Apps canvas app in `powerapps/` | The local form is browser HTML/JavaScript. Power Apps uses controls and Power Fx and writes to SharePoint. |
| `local-sim/web/` manager queue and review dialog | Teams Adaptive Card in `powerautomate/adaptive-card.json` | The local page lists, filters, edits, approves, and rejects requests in one browser UI. Teams presents a card for a flow to wait for one review response. |
| `app.py` HTTP API and route handling | Power Apps plus Power Automate triggers/actions | The local server exposes REST endpoints and serves static files. Microsoft 365 divides those responsibilities between the app, flows, connectors, and hosted services. |
| `service.py` input and review validation | Power Fx validation and Power Automate conditions | Local validation raises Python exceptions. The Microsoft 365 version must repeat important checks in the app and flow because client-side checks alone are not sufficient. |
| `service.py` workflow status changes | Power Automate flow conditions and SharePoint item updates | Python calls the database directly. The cloud flow reads and updates list columns through the SharePoint connector. |
| SQLite `service_requests` table in `database.py` | SharePoint `ServiceRequests` list provisioned from `sharepoint/` | SQLite is a local relational file. SharePoint is a tenant-hosted list with Microsoft 365 permissions, columns, and connector behavior. |
| SQLite transaction that allows review only from `Awaiting review` | Flow condition before the SharePoint update | SQLite uses a write transaction to make the check and update together. The documented cloud approach needs concurrency/version safeguards to offer equivalent protection. |
| `simulated_ai.py` classification | Power Automate **Run a prompt** action for the AI path; simulated Compose actions for the license-free path | Local output is deterministic keyword matching. A prompt can vary and consume AI capacity, so its JSON output needs schema and allow-list checks. The Compose path is a simulation, not AI. |
| `ai/test-set.json` and `local-sim/evaluate_ai.py` | Prompt evaluation before deployment | The local script measures category and priority labels offline. There is no runtime Microsoft 365 component with a direct equivalent; the same test set should be run as a release-quality check. |
| `local-sim/tests/` | Solution test cases and flow/app test runs | Python tests are automated and local. The repository documents Microsoft 365 tests, but no tenant test automation is included. |
| `run-local.ps1` and the Python HTTP server | No direct equivalent | Microsoft 365 hosts the app, list, flow, and Teams experience; there is no single local-style server startup command. |
