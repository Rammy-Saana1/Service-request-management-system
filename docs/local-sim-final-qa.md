# Local prototype final QA

Date: 5 November 2026

Classifier follow-up: 6 November 2026

## Conclusion

The local prototype is suitable for a development freeze: its saved decisions survived a real application restart, manager controls behaved correctly, duplicate decisions were rejected, and all 37 current automated tests pass. No saved request or manager decision was changed.

This conclusion applies only to the local Python/SQLite prototype. It is not a production-readiness claim. Nothing has been connected to or tested in a real Microsoft 365 tenant.

## Evidence supplied by the user

The following results are manual observations reported by the user. They were not created by the QA commands in this review:

| Request | Reported result |
|---|---|
| #1, Laptop not working | Approved; Hardware; High |
| #2, Company internet not working | Approved; Microsoft 365; High |
| #3, Request for new keyboard | Rejected; Hardware; Low |

The user also reported that manager login, approval, and rejection worked and that the pending queue reached zero. No screenshot image files were present in `docs/screenshots/` or `docs/images/` during this review, so screenshots were not independently inspected. Earlier manager screenshots should be treated as outdated because the manager sign-in screen was added later.

## Checks executed in this review

### Persistence and final decisions

Requests #1 through #3 were read through the authenticated local API before and after stopping and restarting the application against the same SQLite file. The selected record fields were identical after restart, including status, category, priority, reviewer, comment, and review timestamp:

| Request | Persisted status | Persisted category | Persisted priority |
|---|---|---|---|
| #1 | Approved | Hardware | High |
| #2 | Approved | Microsoft 365 | High |
| #3 | Rejected | Hardware | Low |

The session created before restart returned HTTP 401 afterward, as expected because sessions are stored only in memory.

### Authorization and review controls

| Check | Actual result |
|---|---:|
| Queue without authentication | HTTP 401 |
| Request detail without authentication | HTTP 401 |
| Decision attempt without authentication | HTTP 401 |
| Login with an incorrect passcode | HTTP 401 |
| Login with the configured passcode | HTTP 200 |
| Session check after login | HTTP 200 |
| Second approval attempt for Request #1 | HTTP 409 |
| Second rejection attempt for Request #3 | HTTP 409 |
| Logout | HTTP 200 |
| Session check after logout | HTTP 401 |

The records were compared before and after the rejected duplicate-decision attempts and were unchanged. A separate temporary server used a one-second session lifetime: the same raw session cookie returned HTTP 200 immediately after login and HTTP 401 after expiry. That expiry check used a temporary database and did not touch the saved requests.

### Request #2 classification difference

Running the current classifier against Request #2's exact saved title and description produces **Network / Critical**. Its final saved values are **Microsoft 365 / High**.

The manager UI fetches a request when its dialog opens, rebuilds both selection lists with that request's values selected, and submits the values currently visible in the form. No cross-request UI state leak was found in that path. The review API deliberately permits a manager to edit category and priority, and finalization stores those edited values.

The database keeps only the final category and priority; it does not retain the original proposal or a field-level edit history. Therefore, the difference is consistent with a manager form edit, including a possible accidental selection, but the available data cannot prove who changed the fields or whether the change was intentional. The saved decision was not modified during QA.

### Simulated classifier

The original tuned evaluation set currently scores 8/8 for category and 8/8 for priority. The holdout regression set also currently scores 8/8 for each, but it is no longer unseen and must not be presented as independent evidence of general accuracy.

The initial exploratory probes found three false positives in the literal rule engine:

- A planned company-wide internet outage next week with a backup connection was still rated Critical.
- A sentence saying the internet is *not* down was rated Critical when it also mentioned all employees.
- Routine phishing-awareness training next month was rated High.

A later requested follow-up added explicit handling for negated incident phrases, planned maintenance without a current incident, and routine security exercises. Six paired regression tests now cover the three reassuring examples and three urgent counterparts. The reassuring examples produce Low, while a current widespread outage and an overrun causing a current outage remain Critical, and a clicked phishing link followed by a suspicious sign-in remains High.

The original tuned evaluation set and the holdout regression set still score 8/8 for category and priority. The holdout is no longer unseen evidence. Manager approval remains mandatory for every result.

### Automated suite

After the classifier follow-up, the complete test command ran **37 tests in 5.807 seconds: 37 passed, 0 failed, 0 errors**.

## Remaining limitations

- The original AI proposal and later manager edits are not recorded separately, so Request #2 cannot be reconstructed conclusively.
- Authentication uses a shared local passcode and self-entered manager name. It is suitable only for this localhost demonstration.
- Sessions are in memory, expire after eight hours, and are intentionally lost on restart.
- The deterministic classifier recognizes only listed wording. More complex negation, unusual maintenance descriptions, security terminology, spelling errors, and contradictory sentences can still be misunderstood.
- Accessibility, multiple browsers, concurrency, crash recovery, database corruption, backup/restore, and long-running use have not been fully tested.
- SQLite remains inside a OneDrive-synchronized project directory. The database is ignored by Git, but this arrangement is not recommended for concurrent or production data.
- The Microsoft 365 design has never been deployed or tested in a real tenant.

No remaining critical bug was identified. The local prototype is ready for a development freeze, provided it remains local, free, and demonstrative rather than being treated as a production or Microsoft 365-validated application.
