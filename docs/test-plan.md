# Test plan

Run tests only with fictional data in a development tenant. Record the flow run ID or screenshot filename as evidence. Restore every temporary formula, JSON value, or connection change after a negative test.

## Test record fields

- Tester: ____________________
- Environment: ____________________
- App version: ____________________
- Flow version/export date: ____________________
- Mode: `Simulated AI` / `Real AI`
- Test date: ____________________

## Canvas app tests

| ID | Test and steps | Expected result | Actual result/evidence | Result |
|---|---|---|---|---|
| APP-01 | Enter valid Title and Description; select Submit once. | One item is created, Requester resolves to the current user, success message includes the item ID, and the form resets. |  | ☐ Pass ☐ Fail |
| APP-02 | Leave Title blank. | Submit is disabled or validation blocks submission; no item is created. |  | ☐ Pass ☐ Fail |
| APP-03 | Enter only spaces in Title. | Custom validation blocks submission; no item is created. |  | ☐ Pass ☐ Fail |
| APP-04 | Leave Description blank, then try spaces only. | Both attempts are blocked; no item is created. |  | ☐ Pass ☐ Fail |
| APP-05 | Enter a Title longer than 120 characters. | Submit is blocked and the user gets a clear length message. |  | ☐ Pass ☐ Fail |
| APP-06 | Enter a Description longer than 2,000 characters. | Submit is blocked and the user gets a clear length message. |  | ☐ Pass ☐ Fail |
| APP-07 | Double-click/tap Submit rapidly with valid data. | Exactly one item is created while `varSubmitting` prevents a second submission. |  | ☐ Pass ☐ Fail |
| APP-08 | Temporarily remove the user's list create permission, then submit. Restore permission afterward. | Form failure message is shown; the form is not reset and no false success is displayed. |  | ☐ Pass ☐ Fail |
| APP-09 | Test All and every Status filter. | Gallery rows match the selected status. |  | ☐ Pass ☐ Fail |
| APP-10 | Search using the beginning of a title; clear the search. Also try summary-only text to confirm it is intentionally not searched. | Title matches display, clearing restores the filtered list, summary-only text does not match, and Studio shows no delegation warning. |  | ☐ Pass ☐ Fail |
| APP-11 | Test with a user whose UPN and mail address differ, if available. | Requester resolves correctly or the limitation is documented and the formula is adjusted. |  | ☐ Pass ☐ Fail |

## Flow and SharePoint tests

| ID | Test and steps | Expected result | Actual result/evidence | Result |
|---|---|---|---|---|
| FLOW-01 | With `Use simulated AI = true`, create a valid item. | Trigger fires once; simulated branch runs; Parse JSON succeeds; row becomes `Awaiting review`; no AI action runs. |  | ☐ Pass ☐ Fail |
| FLOW-02 | Approve the FLOW-01 card without edits. | Row becomes `Approved`; proposal values remain unchanged. |  | ☐ Pass ☐ Fail |
| FLOW-03 | Create another item, edit all allowed fields in the card, and choose Edit and approve. | Valid edits are stored and Status becomes `Approved`. |  | ☐ Pass ☐ Fail |
| FLOW-04 | **Empty description guard:** create an item through a controlled test route that bypasses app validation (temporarily make the list field optional only if necessary). Restore the schema immediately. | Source-data guard does not call a provider; row is routed to manual handling/`Needs edit`; the flow does not generate a reply from empty input. |  | ☐ Pass ☐ Fail |
| FLOW-05 | **Invalid JSON:** temporarily change simulated Compose to the string `{not-json`, run once, then restore the valid object. | Object conversion or Parse JSON fails; Catch runs; row becomes `Needs edit` with neutral fallback text. |  | ☐ Pass ☐ Fail |
| FLOW-06 | **Missing property:** temporarily return an object without `suggestedReply`. | Parse JSON fails because the required property is missing; Catch runs. |  | ☐ Pass ☐ Fail |
| FLOW-07 | **Unknown category:** temporarily return `category = Facilities`. | Validation changes Category to `Other`; the raw invalid category is not written to the Choice field. |  | ☐ Pass ☐ Fail |
| FLOW-08 | **Unknown priority:** temporarily return `priority = Emergency`. | Validation changes Priority to `Medium`; the invalid value is not written. |  | ☐ Pass ☐ Fail |
| FLOW-09 | Return summary/reply values over their limits. | Stored/card values are truncated to the documented safe lengths; flow succeeds. |  | ☐ Pass ☐ Fail |
| FLOW-10 | Temporarily break or disable the provider action in the active branch. | Try fails and Catch routes the item to `Needs edit`; failure is visible to operators. |  | ☐ Pass ☐ Fail |
| FLOW-11 | Temporarily use a SharePoint connection without update permission. | Run shows the Update item failure. If Catch also fails, the limitation is visible in run history and documented; no false Approved status appears. |  | ☐ Pass ☐ Fail |
| FLOW-12 | Submit two valid list items close together. | Two independent flow runs update the correct IDs; values do not cross between items. |  | ☐ Pass ☐ Fail |
| FLOW-13 | Turn on the flow, edit an existing item, and observe runs. | No new run occurs because the trigger is create-only. |  | ☐ Pass ☐ Fail |
| FLOW-14 | Set `Use simulated AI = false` before configuring the real branch. | The placeholder object fails the required-property Parse JSON check and routes to Catch; the flow does not silently pretend AI ran. |  | ☐ Pass ☐ Fail |

## Teams Adaptive Card tests

| ID | Test and steps | Expected result | Actual result/evidence | Result |
|---|---|---|---|---|
| CARD-01 | Run the simulated happy path in the standard `Triage Review` channel. | Card renders in desktop/web Teams, declares `SIMULATED AI`, and shows all inputs/actions. |  | ☐ Pass ☐ Fail |
| CARD-02 | Submit a card, then have another reviewer try the old controls. | Only the first response changes the item; handled card is replaced/updated so it no longer appears actionable. |  | ☐ Pass ☐ Fail |
| CARD-03 | Use source/proposal text containing quotes, backslashes, ampersands, Unicode, and line breaks. | Card JSON remains valid and text renders without losing meaning or exposing markup. If it fails, change payload construction and retest. |  | ☐ Pass ☐ Fail |
| CARD-04 | Inspect the successful wait-action Outputs. | Actual paths for action and each edited field are recorded in `docs/audit-notes.md` and match all downstream expressions. |  | ☐ Pass ☐ Fail |
| CARD-05 | Open on Teams mobile if available. | Schema 1.4 card renders and can be submitted; any client limitation is documented. |  | ☐ Pass ☐ Fail ☐ N/A |
| CARD-06 | Attempt to select a private channel in a throwaway action; do not change the real action. | Private-channel posting is unavailable/unsupported, confirming why the solution uses a standard channel in a restricted Team. |  | ☐ Pass ☐ Fail ☐ N/A |

## Real-AI prompt tests

Run these only when the real branch and capacity are available. Use `ai/test-set.json` as the source and compare with its expected output. A valid JSON response must contain exactly usable string values for category, priority, summary, and suggestedReply after parsing.

| Test ID | Expected category | Actual category | Category correct? | Expected priority | Actual priority | Priority correct? | JSON valid? | Summary factual? | Reply supported/safe? | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| T01 | Microsoft 365 |  | ☐ | Medium |  | ☐ | ☐ | ☐ | ☐ |  |
| T02 | Network |  | ☐ | Critical |  | ☐ | ☐ | ☐ | ☐ |  |
| T03 | Software |  | ☐ | Low |  | ☐ | ☐ | ☐ | ☐ |  |
| T04 | Access |  | ☐ | High |  | ☐ | ☐ | ☐ | ☐ |  |
| T05 | Hardware |  | ☐ | Low |  | ☐ | ☐ | ☐ | ☐ |  |
| T06 | Software |  | ☐ | Medium |  | ☐ | ☐ | ☐ | ☐ |  |
| T07 | Other |  | ☐ | Low |  | ☐ | ☐ | ☐ | ☐ |  |
| T08 | Hardware |  | ☐ | Low |  | ☐ | ☐ | ☐ | ☐ |  |

### AI quality summary

- Valid JSON rate: ______ / ______ = ______%
- Category accuracy: ______ / ______ = ______%
- Priority accuracy: ______ / ______ = ______%
- Critical-request recall: correctly predicted Critical ______ / expected Critical ______ = ______%
- Factual summaries: ______ / ______ = ______%
- Supported/safe replies: ______ / ______ = ______%
- Prompt/model/configuration and version: __________________________________
- Decision: ☐ Accept for human-reviewed pilot ☐ Revise and rerun ☐ Block
- Main observed failure modes: _____________________________________________

## Exit criteria

- All APP, FLOW, and CARD tests required for the available clients pass, or each failure has an owner and documented mitigation.
- No test writes an out-of-list category/priority or marks a failed run Approved.
- Simulated mode is visibly distinguished from real AI.
- If real AI is used: JSON validity is 100%, Critical recall target is agreed and met, and every reply remains human-reviewed.
- Temporary negative-test edits and permissions have been restored.
