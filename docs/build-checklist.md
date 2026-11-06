# Tenant build checklist

Use this order. Do not enable the real-AI branch until the simulated path passes. Record a date, result (`Pass`, `Fail`, or `Blocked`), and evidence such as a screenshot name or flow-run URL in every Outcome field.

## 1. Tenant and environment

- [ ] **1.1 Confirm a development-only Microsoft 365 tenant and maker account.** Do not use production data.
  - How to know it worked: the account can open SharePoint, Teams, `make.powerapps.com`, and `make.powerautomate.com` in the same tenant.
  - Outcome/date/evidence: ________________________________________________
- [ ] **1.2 Confirm a Power Platform environment and region.**
  - How to know it worked: the intended environment appears in both maker portals and is selected in the environment picker.
  - Outcome/date/evidence: ________________________________________________
- [ ] **1.3 Check DLP and app policy.** Confirm SharePoint and Teams may be used together and that the Teams **Workflows** app is allowed.
  - How to know it worked: connections can be created and Workflows is available in Teams.
  - Outcome/date/evidence: ________________________________________________
- [ ] **1.4 Record the AI decision.** Start with simulated mode. Separately record whether AI Builder/Copilot capacity is available.
  - How to know it worked: the build log says `Use simulated AI = true`; no paid connector is required for the first pass.
  - Outcome/date/evidence: ________________________________________________

## 2. SharePoint and Teams locations

- [ ] **2.1 Create or choose the `Service Desk Lab` SharePoint team site.**
  - How to know it worked: the maker can open Site contents and create a temporary list or has equivalent permission.
  - Outcome/date/evidence: ________________________________________________
- [ ] **2.2 Create a private-membership Team named `Service Desk Lab`.** Add only fictional test users.
  - How to know it worked: requester/reviewer test accounts have the intended membership and unrelated accounts do not.
  - Outcome/date/evidence: ________________________________________________
- [ ] **2.3 Create a standard channel named `Triage Review`.** Do not use a private channel; the connector does not support posting cards there.
  - How to know it worked: the flow owner sees the Team and channel in the Teams connector selectors.
  - Outcome/date/evidence: ________________________________________________

## 3. SharePoint list

- [ ] **3.1 Install PnP.PowerShell under PowerShell 7.4.0 or later.**
  - How to know it worked: `$PSVersionTable.PSVersion` is at least 7.4.0 and `Get-Command Connect-PnPOnline` succeeds.
  - Outcome/date/evidence: ________________________________________________
- [ ] **3.2 Register/identify the tenant Entra application client ID for interactive PnP login.**
  - How to know it worked: `Connect-PnPOnline -Interactive -ClientId ...` opens sign-in and connects to the target site.
  - Outcome/date/evidence: ________________________________________________
- [ ] **3.3 Run `sharepoint/provision-ServiceRequests.ps1`.**
  - How to know it worked: it completes without an error and `ServiceRequests` appears in Site contents.
  - Outcome/date/evidence: ________________________________________________
- [ ] **3.4 Inspect the schema manually.** Check Title, Description, Requester, Category, Priority, AISummary, SuggestedReply, Status, and Created.
  - How to know it worked: choice values match `sharepoint/README.md`; Description's internal name is `RequestDescription`; Status defaults to `New`.
  - Outcome/date/evidence: ________________________________________________
- [ ] **3.5 Create one manual test row with a valid tenant user.**
  - How to know it worked: SharePoint resolves Requester as a Person and saves Title/Description with Status `New`.
  - Outcome/date/evidence: ________________________________________________

## 4. Cloud flow in simulated mode

- [ ] **4.1 Create an automated flow and add SharePoint `When an item is created`.** Select the site/list from the selectors.
  - How to know it worked: creating a temporary item produces one flow run. It may fail later until the flow is complete.
  - Outcome/date/evidence: ________________________________________________
- [ ] **4.2 Add top-level variables.** Add Boolean `Use simulated AI = true` and Object `AI response = {}`.
  - How to know it worked: the run history shows both initialized values and the Boolean is true.
  - Outcome/date/evidence: ________________________________________________
- [ ] **4.3 Build the Try scope, source-data guard, and provider switch from `powerautomate/flow-build-guide.md`.**
  - How to know it worked: a valid item follows the simulated Yes branch; the real branch is not called.
  - Outcome/date/evidence: ________________________________________________
- [ ] **4.4 Add `Simulated AI response` Compose and assign it to `AI response`.**
  - How to know it worked: the Object variable contains exactly category, priority, summary, and suggestedReply.
  - Outcome/date/evidence: ________________________________________________
- [ ] **4.5 Add Parse JSON with `powerautomate/parse-json-schema.json`, allow-list validation, and length trimming.**
  - How to know it worked: a valid object stays valid; a temporary `Facilities` category becomes `Other`.
  - Outcome/date/evidence: ________________________________________________
- [ ] **4.6 Add the first SharePoint Update item.** Preserve required source values.
  - How to know it worked: the row contains the proposal and Status becomes `Awaiting review` for valid source data.
  - Outcome/date/evidence: ________________________________________________

## 5. Teams review card

- [ ] **5.1 Add current Teams action `Post adaptive card and wait for a response`.** Choose the Flow bot if supported, channel location, private Team, and standard `Triage Review` channel.
  - How to know it worked: the action saves without a deprecated-action warning and its selectors resolve.
  - Outcome/date/evidence: ________________________________________________
- [ ] **5.2 Paste `powerautomate/adaptive-card.json` and map the proposal fields.**
  - How to know it worked: the card renders in Teams, says `SIMULATED AI`, and displays editable values.
  - Outcome/date/evidence: ________________________________________________
- [ ] **5.3 Submit Approve and inspect the Teams action Outputs.** Record the exact response paths/tokens.
  - How to know it worked: the output identifies the action and input values; the guide expressions are confirmed or corrected together.
  - Outcome/date/evidence: ________________________________________________
- [ ] **5.4 Add the final validation and SharePoint Update item.**
  - How to know it worked: approved/edited values are saved, Status is `Approved`, and reviewer/timestamp behavior matches the design.
  - Outcome/date/evidence: ________________________________________________
- [ ] **5.5 Replace/update the handled card.**
  - How to know it worked: a second person cannot submit the already handled card and receives no misleading active controls.
  - Outcome/date/evidence: ________________________________________________
- [ ] **5.6 Add the Catch scope and configure Run after for failed, timed out, and skipped.**
  - How to know it worked: deliberately malformed simulated JSON sends the row to `Needs edit` and posts a neutral alert.
  - Outcome/date/evidence: ________________________________________________

## 6. Canvas app

- [ ] **6.1 Create the canvas app and add the `ServiceRequests` SharePoint data source.**
  - How to know it worked: the list appears in Data and a gallery can display the manual test row.
  - Outcome/date/evidence: ________________________________________________
- [ ] **6.2 Build `frmRequest` with Title, Description, and Requester.** Apply the documented control names and Requester Update formula.
  - How to know it worked: a preview shows the three inputs and resolves the signed-in maker as Requester.
  - Outcome/date/evidence: ________________________________________________
- [ ] **6.3 Apply validation, display-mode, submit, success, and failure formulas from `powerapps/`.**
  - How to know it worked: blank/overlength input is blocked; a valid submit creates exactly one item and shows its ID.
  - Outcome/date/evidence: ________________________________________________
- [ ] **6.4 Build the Requests screen and apply status/search/sort formulas.**
  - How to know it worked: All and individual status filters return the correct rows; prefix search finds matching titles; Studio shows no delegation warning. AI Summary is intentionally display-only to preserve delegation.
  - Outcome/date/evidence: ________________________________________________
- [ ] **6.5 Save, publish, and share the app plus SharePoint permissions.**
  - How to know it worked: the requester test account opens the published app and can create only the data allowed by the prototype permission model.
  - Outcome/date/evidence: ________________________________________________

## 7. End-to-end simulated proof

- [ ] **7.1 Run `APP-01`, `FLOW-01`, `CARD-01`, and `CARD-02` from the test plan.**
  - How to know it worked: all pass and their evidence is recorded in `docs/test-plan.md`.
  - Outcome/date/evidence: ________________________________________________
- [ ] **7.2 Run every failure-path test and restore temporary changes.**
  - How to know it worked: malformed/provider failures route to `Needs edit`; invalid labels are safely defaulted; the flow definition is restored.
  - Outcome/date/evidence: ________________________________________________
- [ ] **7.3 Capture redacted screenshots.**
  - How to know it worked: all five files requested by `docs/images/README.md` exist and contain no tenant secrets or real personal data.
  - Outcome/date/evidence: ________________________________________________

## 8. Optional real-AI branch

- [ ] **8.1 Confirm entitlement, capacity, region, and DLP before adding AI Builder.**
  - How to know it worked: the environment exposes Prompt Builder and `Run a prompt`, and an administrator confirms usable capacity.
  - Outcome/date/evidence: ________________________________________________
- [ ] **8.2 Create `Service Request Triage v1` as Text output and add the prompt/examples.**
  - How to know it worked: Prompt Builder tests return one four-field JSON object without extra prose.
  - Outcome/date/evidence: ________________________________________________
- [ ] **8.3 Add `Run a prompt` to the real branch and map the generated Text token.** Set `Use simulated AI = false` for the test.
  - How to know it worked: run history proves the AI action ran, the simulated action did not, and the card says `REAL AI`.
  - Outcome/date/evidence: ________________________________________________
- [ ] **8.4 Execute the AI test set and calculate the metrics in `docs/test-plan.md`.**
  - How to know it worked: all actual outputs, JSON validity, label accuracy, critical-request recall, and qualitative checks are recorded.
  - Outcome/date/evidence: ________________________________________________

## 9. Handoff

- [ ] **9.1 Export backups and remove secrets/tenant identifiers from repository artifacts.**
  - How to know it worked: a fresh `git diff` review shows no credentials, connection IDs, run URLs, real names, or sensitive request text.
  - Outcome/date/evidence: ________________________________________________
- [ ] **9.2 Fill in README Lessons learned and the unresolved audit items.**
  - How to know it worked: each real issue has evidence, root cause, fix, and retest result—not just a success claim.
  - Outcome/date/evidence: ________________________________________________
