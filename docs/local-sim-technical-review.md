# Local simulation technical review

## Scope and conclusion

This review covers the browser UI, Python HTTP server, workflow service, SQLite persistence, deterministic classifier, and manager approval path. The application remains a local Windows prototype. It is **not production-ready** and has not been tested in a real Microsoft 365 tenant.

## Prioritized findings

| Priority | Finding | Status |
|---|---|---|
| High | Queue, request details, and decisions were available without authorization. | Fixed with a server-enforced manager session. |
| High | The browser supplied `reviewed_by`, allowing reviewer-name spoofing. | Fixed; reviewer identity now comes from the authenticated session. |
| High | Priority missed number-word deadlines and misunderstood explicit negation. | Fixed with general patterns and regression tests. |
| Medium | Non-string JSON values were silently converted to text. | Fixed; text fields now reject objects, arrays, booleans, and null. |
| Medium | SQLite constrained status only; invalid category/priority or incomplete review metadata could be written outside the service. | Fixed for future inserts/updates with database triggers. |
| Medium | Wrong content types, invalid UTF-8, and SQLite request failures did not produce consistent JSON errors. | Fixed with controlled 400/500 responses. |
| Medium | The server could be deliberately bound beyond the local computer and omitted basic browser security headers. | Fixed with loopback-only binding, CSP, `nosniff`, referrer, and permissions headers. |
| Medium | Manager UI lacked sign-in, complete tab keyboard behavior, clear focus movement, and assertive error announcements. | Improved; formal assistive-technology testing remains open. |
| Low | There is no backup, encrypted storage, schema migration framework, or immutable audit history. | Open prototype limitation. |

## Significant changes

### Authorization and approval

- `run-local.ps1` prompts for a passcode of at least 12 characters unless `LOCAL_SIM_MANAGER_PASSCODE` is already set.
- Manager login creates a random, HTTP-only, SameSite session cookie. Sessions are kept in memory, expire after eight hours, and disappear on restart.
- Queue, detail, and decision endpoints return HTTP 401 without a valid session.
- The manager name is captured at login and injected by the server during a decision. A caller-provided `reviewed_by` value is ignored.
- The existing immediate SQLite transaction still permits a request to be finalized only once. Manager approval remains mandatory for every proposal, including High and Critical priorities.

### Validation, errors, and persistence

- JSON API requests must use `application/json`, valid UTF-8, an object payload, and the existing body-size limit.
- Business text fields must be strings and retain their required/minimum/maximum checks.
- SQLite triggers enforce category, priority, AI mode, field lengths, review metadata, and rejection-reason integrity even if the Python service is bypassed.
- Expected database failures return a generic HTTP 500 response without exposing SQL details.
- Persistence was tested by closing and reopening the database and reading the created row.

### Simulated AI

- Near deadlines now recognize number words from one through twelve for minutes and hours.
- Explicit phrases such as “nothing is blocked today” suppress the otherwise misleading `today` urgency signal.
- Explicitly negated outages, planned future maintenance with a fallback, and routine security training no longer inherit emergency priority solely from words such as `down`, `outage`, or `phishing`. Paired tests retain Critical/High results for corresponding active incidents.
- The original set is tuned and scores 8/8 after the change. The first genuinely unseen holdout run remains 6/8; a later regression rerun after analyzing H04 and H05 scores 8/8 and is not presented as unseen evidence.

### User interface and accessibility

- The manager view now shows a sign-in form before protected data.
- Tabs expose tab roles, relationships, selected state, roving tab stops, and Left/Right Arrow navigation.
- Errors switch to assertive alert announcements, buttons and links have visible keyboard focus, and focus moves to the manager queue after login.
- Pressing Enter in the review dialog no longer closes it without an explicit approve/reject action.
- A formal WCAG audit, screen-reader test, zoom/reflow test, and cross-browser test have not been completed.

## Automated verification

The latest local run completed **37 tests with 37 passing**. This includes the previous security, validation, persistence, workflow, and priority coverage plus six paired regression tests for negated outages, planned maintenance, routine security training, and corresponding genuine incidents.

AI results after the fixes:

| Data set | Category | Priority | Overall labels | Exact cases |
|---|---:|---:|---:|---:|
| Original set (tuned) | 8/8 | 8/8 | 16/16 | 8/8 |
| First holdout run (one-time, unseen; before H04/H05 fixes) | 8/8 | 6/8 | 14/16 | 6/8 |
| Holdout regression rerun (not unseen) | 8/8 | 8/8 | 16/16 | 8/8 |

## What still needs improvement

- Replace the shared passcode and self-declared manager name with a real identity provider before any multi-user or networked use.
- Add login throttling/account lockout, credential lifecycle handling, CSRF tokens, TLS, and security logging before treating authentication as production-grade.
- Add versioned database migrations, backups, restore testing, encryption requirements, and an append-only audit history.
- Move the runtime database out of a cloud-synchronized project folder or explicitly test that storage arrangement. SQLite locking and OneDrive file synchronization are not a supported backup/concurrency design.
- Test accessibility with keyboard-only use, a screen reader, 200–400% zoom, reduced-motion settings, and more than one browser.
- Expand AI evaluation with larger, independently labeled data that is not used for rule development.
- Perform concurrency, load, long-running persistence, crash-recovery, and corrupted-database tests.
- Add pagination/search for a large queue and a deliberate backup/export/reset workflow if the prototype will retain more than disposable test data.
- Keep the service bound to localhost and use fictional data. The current controls reduce local risk but do not justify a production-readiness claim.
