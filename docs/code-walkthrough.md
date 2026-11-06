# Local simulation code walkthrough

The local simulation separates the web server, workflow rules, classification rules, and storage. A request normally travels through them in this order:

`browser -> app.py -> service.py -> simulated_ai.py -> database.py`

During review, the path is `browser -> app.py -> service.py -> database.py`.

## `app.py`: the web and API entry point

`app.py` starts a small Python HTTP server that is restricted to the local computer. It serves the files in `local-sim/web/` and exposes API routes that the browser calls. `POST /api/requests` creates an employee request. Listing requests, reading one request, and recording a decision require a manager session created with the local startup passcode.

The manager session is an unpredictable token in an HTTP-only cookie. It expires after eight hours or when the server stops. The manager name is stored with the server-side session, so changing `reviewed_by` in a request cannot impersonate somebody else. This is useful local protection, not a replacement for enterprise identity.

The server requires UTF-8 JSON with the correct content type, a body below the size limit, and an object at the top level. It adds basic browser security headers and then hands business work to `RequestService`. Its `_execute` helper turns service exceptions into useful HTTP responses: validation becomes 400, missing data becomes 404, an unauthenticated manager request becomes 401, and a repeated review becomes 409.

The important handoff for a new request is:

```python
service.create(self._read_json())
```

`app.py` does not classify requests or write SQL itself.

## `service.py`: workflow rules and validation

`RequestService` is the middle layer shared by the API and tests. It requires actual JSON strings instead of converting objects, arrays, booleans, or null values into text. It checks required fields and their maximum lengths. Creation also requires a description of at least 20 characters. Review validation checks the decision, authenticated reviewer, rejection reason, supported category and priority, and the lengths of the edited summary and reply.

Classification starts here, but the rules live elsewhere:

```python
proposal = classify(title, description)
```

The returned proposal is saved with the request. During a decision, omitted proposal fields keep their current values, while supplied edits are checked before saving. A rejection must include a reason.

The helper `_required_text` contains the common “required” and maximum-length checks. This keeps the same rules from being copied for title, description, requester, and reviewer.

## `simulated_ai.py`: deterministic classification

Despite its name, this file does not call a model. `classify` combines rule-based category, priority, summary, and reply functions into the same four-field shape expected from the Microsoft 365 design.

Category selection counts keyword matches. A title match is worth three description matches, because the title usually identifies the affected service. If nothing matches, the category is `Other`; tuple order breaks a tied score.

Priority selection groups text patterns into explainable signals: severe risk, affected-user scope, outage or blocked work, stopped operations, lack of a workaround, deadline distance, and low-urgency or strong-workaround evidence. Before those signals are scored, a small list of explicitly negated incident phrases is removed; planned maintenance and routine security exercises also need current-incident evidence before they can inherit emergency priority. Severe risk and broad impact take precedence, blocked time-sensitive work can become High, clearly planned or well-covered work can become Low, and ambiguous cases remain Medium. This stays repeatable but can still miss unfamiliar wording or complex negation. The summary uses the title and first description sentence, and the reply is a fixed template selected by category.

## What prevents two reviews

The final safeguard is in `database.py`, not the browser. `review_request` starts an immediate SQLite write transaction, reads the current status, and accepts only `Awaiting review`:

```python
if current["status"] != "Awaiting review":
    raise RuntimeError("This request has already been reviewed.")
```

Because the check and update happen while that transaction holds the write lock, two reviewers cannot both successfully finalize the same request. `service.py` converts the runtime error to `ConflictError`, and `app.py` returns HTTP 409 to the later reviewer. SQLite triggers also reject unsupported categories, priorities, invalid field lengths, or a final status without review metadata. The database checks, rather than disabled browser buttons, enforce these rules.
