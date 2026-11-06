# Real-world implementation audit

Audit date: 25 October 2026. This is a documentation and static-file audit; nothing in this repository has yet been run in the target tenant.

## Status key

- **verified from docs** — the name, behavior, or requirement is stated in current Microsoft or PnP documentation linked below.
- **likely correct** — consistent with current product behavior and syntax, but the exact generated control, token, or tenant configuration must be tested.
- **uncertain** — public documentation does not guarantee the exact behavior or it depends on the tenant/designer. A specific build-time check is identified.

## Clear errors corrected

| Finding | Status | Correction |
|---|---|---|
| The guide selected a private Teams channel. The Teams connector states that posting messages or Adaptive Cards to private channels is unsupported. | **verified from docs** | Use a private-membership Team with a **standard** `Triage Review` channel. |
| The setup said only “PowerShell 7.” Current PnP.PowerShell requires PowerShell 7.4.0 or later. | **verified from docs** | Added a 7.4.0 guard to the script and deployment steps. |
| The deployment guide told the maker to apply `ai/output-schema.json` to AI Builder JSON output. The prompt editor generates its JSON format from an example; it does not accept this repository schema as an editable schema. | **verified from docs** | The primary flow now uses generated **Text** plus Parse JSON. Native JSON output is documented as an optional alternative requiring token changes. |
| The flow previously had no executable no-capacity path. | **verified from docs** for Compose availability; solution change | Added `Use simulated AI`, a hardcoded Compose object, and a visible card mode label. |
| A strict 2020-12 JSON schema was presented as the runtime Power Automate schema without confirmed draft support. | **uncertain** | Kept it as the AI contract/offline validation schema and added a conservative `powerautomate/parse-json-schema.json`; allow lists and lengths are enforced with expressions. |
| A failed **Terminate** action was considered as the unconfigured-provider guard. Terminate ends the run, so a later Catch scope would not handle it. | **verified from docs** | The placeholder now supplies an intentionally incomplete object; Parse JSON fails inside Try and Catch can run. |
| Search-input delay settings can differ between classic and modern controls. | **verified from docs** | Documented `DelayOutput = true` for classic Text input and `TriggerOutput = TriggerOutput.Delayed` for modern Text input. |

## Connector and action audit

| Claim | Status | Build-time proof |
|---|---|---|
| SharePoint connector actions **When an item is created** and **Update item** exist, and the connector is Standard. | **verified from docs** | Both actions appear after selecting the SharePoint connector. |
| Microsoft Teams connector is Standard. | **verified from docs** | The connector reference labels it Standard. |
| Current wait action is **Post adaptive card and wait for a response** (`PostCardAndWaitForResponse`). The older channel-specific wait action is deprecated. | **verified from docs** | Select the non-deprecated action and confirm its poster/location controls. |
| A Flow bot can post to a standard channel, but private-channel posting is unsupported. Flow bot posting is unavailable in GCC, GCC High, and DoD. | **verified from docs** | Target a standard channel; confirm the tenant cloud supports the chosen poster. |
| The Teams Workflows app must be allowed, and the connector has an approximate 28 KB message-size limit. | **verified from docs** | Save the action and send the repository card successfully. |
| Only one user can successfully submit a wait card; updating/replacing the card prevents misleading later clicks. | **verified from docs** | Submit once and verify a second submission cannot alter the item. |
| AI Builder's current cloud-flow action is **Run a prompt**; generated text is available through the **Text** token. | **verified from docs** | Add the action and choose its generated Text dynamic-content token. |
| Azure OpenAI is a Premium connector. | **verified from docs** | The connector is marked Premium in the maker UI/reference. |
| The exact Teams response expression `body('Post_adaptive_card_and_wait_for_a_response')?['data']?...` is stable. | **uncertain** | Submit one card, inspect the action Outputs in run history, and use designer dynamic content where offered. Adjust every response expression together. |
| `Requester Claims` is the correct value for **Update item** in this generated list action. | **uncertain** | Inspect the trigger and Update item fields in the target tenant. Preserve the original Requester with the designer's accepted Person token. |

## Expression audit

| Item | Status | Notes |
|---|---|---|
| `triggerBody`, `outputs`, `body`, `coalesce`, `empty`, `trim`, `contains`, `createArray`, `take`, `if`, `and`, `equals`, and `formatDateTime` | **verified from docs** | These are documented Workflow Definition Language functions used by Power Automate. |
| `decodeUriComponent('%0A')` to produce a newline | **verified from docs** | `decodeUriComponent` is documented; the expression cookbook documents this newline pattern. |
| Data Operations **Parse JSON** exists. | **verified from docs** | Use the repository's conservative runtime schema. |
| `json(outputs('Clean_AI_JSON'))` converts cleaned text to an object and fails on malformed JSON. | **verified from docs** | Use this in the real-provider branch before setting the Object variable. |
| Run-after supports failed, timed out, skipped, and successful states for error handling. | **verified from docs** | Configure the Catch scope in the designer and deliberately fail parsing. |
| The designer will serialize dynamic values inserted directly into the Adaptive Card JSON safely when text contains quotes, backslashes, or newlines. | **uncertain** | Run test `CARD-03`; if the card fails, construct/escape the payload using designer tokens or a composed object rather than raw string interpolation. |

## PnP PowerShell audit

| Item | Status | Notes |
|---|---|---|
| PnP.PowerShell requires PowerShell 7.4.0 or later. | **verified from docs** | The script now fails early on older versions. |
| `Connect-PnPOnline -Url -Interactive -ClientId`, `Get-PnPList`, `New-PnPList -Template GenericList -OnQuickLaunch`, `Add-PnPField`, and `Set-PnPField` exist. | **verified from docs** | Names and principal parameters match current PnP references. |
| Interactive login requires an app/client ID; `Register-PnPEntraIDAppForInteractiveLogin` and `-SharePointDelegatePermissions` exist. | **verified from docs** | Registration still depends on tenant permission to create/consent to the app. |
| `Add-PnPField -Type Note/User/Choice/Text`, `-Choices`, `-Required`, and `-AddToDefaultView` are accepted parameters. | **verified from docs** | The field definitions match documented parameters. |
| `Set-PnPField -Values @{ Indexed = $true }` and setting `DefaultValue` will behave exactly as intended in this tenant. | **likely correct** | Current cmdlet accepts a Values hashtable, but verify the resulting Indexed and default properties after provisioning. |
| A second run is fully idempotent for every changed field property. | **likely correct** | It avoids duplicate list/fields, but does not reconcile all possible manual schema changes. Review warnings and the resulting list. |

## Power Fx audit

| Item | Status | Notes |
|---|---|---|
| `SubmitForm`, `NewForm`, `ResetForm`, `Refresh`, `Notify`, `Navigate`, `Set`, `Filter`, `StartsWith`, `SortByColumns`, `IsBlank`, `Len`, `Trim`, `Lower`, `User`, `If`, and `IfError` are valid functions; `Form.Valid`, `Form.Error`, and `Form.LastSubmit` are valid form properties. | **verified from docs** | The formulas use supported names and separators for an en-US authoring locale. |
| `User().Email` returns the current user's UPN, not necessarily the SMTP address. | **verified from docs** | Acceptable for many SharePoint users, but test guests/UPN-mail differences. |
| `Filter` equality, text `StartsWith`, and `SortByColumns` can delegate to SharePoint. | **verified from docs** | Confirm that Studio shows no delegation warning for the final expression. |
| `Status.Value = ddStatus.Selected.Value` delegates with the generated SharePoint Choice column/control. | **likely correct** | Exact delegation/control shape is data-source and control dependent; test with more than the nondelegation row limit. |
| A manually constructed `SPListExpandedUser` record is accepted by the generated Requester card. | **likely correct** | Common SharePoint canvas-app pattern; confirm a submitted item resolves the maker account as a Person. |
| `txtTitle.Text`, `txtDescription.Text`, and `ddStatus.Selected.Value` match the controls the maker creates. | **likely correct** | The guide now recommends matching classic controls; modern/generated controls may expose different properties. |

## Adaptive Card audit

| Item | Status | Notes |
|---|---|---|
| Teams desktop, web, and mobile support Adaptive Card schema 1.5; this card declares 1.4. | **verified from docs** | Version 1.4 is within the documented supported level. |
| `Input.ChoiceSet` supports `choices`, `value`, `style`, `isRequired`, `errorMessage`, and labels at the declared version. | **verified from docs** | `isRequired` and `errorMessage` require 1.3; the card uses 1.4. |
| `Action.Submit` data can distinguish Approve from Edit and approve. | **verified from docs** | Inspect the response once to confirm where Teams places the action data. |
| `msteams.width = Full` is supported by Teams. | **verified from docs** | It is a Teams-specific card extension. |

## File-by-file review

| File | Result |
|---|---|
| `.gitignore` | **likely correct** — excludes common local/export secrets; still inspect exports before committing. |
| `README.md` | **likely correct** — case study and licensing language aligned with simulated/real modes. |
| `docs/solution-design.md` | **likely correct** — architecture and trade-offs consistent; tenant governance remains local. |
| `docs/responsible-ai.md` | **likely correct** — controls align with human review and fictional-data scope. |
| `docs/deployment-guide.md` | **likely correct** — corrected private-channel, PnP, JSON-output, and fallback guidance. |
| `docs/audit-notes.md` | **likely correct** — static audit with sources and explicit tenant-verification boundaries. |
| `docs/build-checklist.md` | **likely correct** — manual instructions must still be exercised in the target tenant. |
| `docs/test-plan.md` | **likely correct** — covers functional and failure paths; expected results require tenant execution. |
| `docs/interview-prep.md` | **likely correct** — model answers are bounded by the documented implementation. |
| `docs/images/README.md` | **likely correct** — documentation-only capture guidance. |
| `sharepoint/provision-ServiceRequests.ps1` | **likely correct** — cmdlets/parameters verified; requires live tenant validation noted above. |
| `sharepoint/sample-requests.csv` | **likely correct** — static CSV; example identities must be replaced before Person-field import. |
| `sharepoint/README.md` | **likely correct** — schema documentation matches the script. |
| `powerapps/README.md` | **likely correct** — control assumptions are now explicit. |
| `powerapps/app-onstart.powerfx` | **verified from docs** for functions; exact app locale/control integration is **likely correct**. |
| `powerapps/gallery-items.powerfx` | **likely correct** — verify delegation warning and Choice control shape. |
| `powerapps/request-form-events.powerfx` | **verified from docs** for form APIs; notification/navigation behavior is **likely correct**. |
| `powerapps/requester-datacard-update.powerfx` | **likely correct** — tenant Person record acceptance needs a submission test. |
| `powerapps/screen-onvisible.powerfx` | **verified from docs** for `Refresh`; integration is **likely correct**. |
| `powerapps/submit-button-displaymode.powerfx` | **verified from docs** for functions/properties; control names are **likely correct**. |
| `powerapps/submit-button-onselect.powerfx` | **verified from docs** for functions/properties; control names are **likely correct**. |
| `powerautomate/flow-build-guide.md` | **likely correct** overall; response-token and Person-token items remain **uncertain**. |
| `powerautomate/adaptive-card.json` | **verified from docs** for schema elements; runtime dynamic-text escaping is **uncertain**. |
| `powerautomate/parse-json-schema.json` | **likely correct** — intentionally uses a conservative subset; validate in the designer. |
| `ai/system-prompt.md` | **likely correct** — prompt behavior must be measured, not assumed. |
| `ai/few-shot-examples.md` | **likely correct** — examples follow the contract. |
| `ai/output-schema.json` | **likely correct** as a JSON Schema 2020-12/offline contract; not claimed as an editable AI Builder schema. |
| `ai/test-set.json` | **likely correct** — valid static test data; expected labels are human-authored baselines. |
| `ai/README.md` | **likely correct** — distinguishes offline and runtime schemas. |

## Claims still requiring tenant verification

1. The exact Teams wait-action response paths for `action`, `editedCategory`, `editedPriority`, `editedSummary`, and `editedReply`.
2. The exact SharePoint Person dynamic-content token accepted by **Update item** for Requester.
3. Whether request text containing quotes, backslashes, Unicode, or newlines renders safely in the card payload.
4. Whether the target designer accepts the conservative Parse JSON schema unchanged.
5. The resulting `Indexed` and `DefaultValue` field properties after the PnP script runs.
6. The generated Power Apps control property names, Person record acceptance, and absence of delegation warnings.
7. Tenant-specific licensing, capacity, region, DLP policy, Workflows-app policy, and government-cloud limitations.

## Primary references

- [Microsoft Teams connector](https://learn.microsoft.com/en-us/connectors/teams/)
- [Adaptive Cards in Power Automate](https://learn.microsoft.com/en-us/power-automate/overview-adaptive-cards)
- [Teams Adaptive Card support](https://learn.microsoft.com/en-us/microsoftteams/platform/task-modules-and-cards/cards/cards-format)
- [Adaptive Card ChoiceSet schema](https://learn.microsoft.com/en-us/adaptive-cards/schema-explorer/input-choice-set)
- [SharePoint connector](https://learn.microsoft.com/en-us/connectors/sharepointonline/)
- [Use a custom prompt in a flow](https://learn.microsoft.com/en-us/ai-builder/use-a-custom-prompt-in-flow)
- [Prompt JSON output](https://learn.microsoft.com/en-us/microsoft-copilot-studio/process-responses-json-output)
- [Workflow expression reference](https://learn.microsoft.com/en-us/azure/logic-apps/expression-functions-reference)
- [Power Automate expression cookbook](https://learn.microsoft.com/en-us/power-automate/expression-cookbook)
- [Power Automate error handling](https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/error-handling)
- [Power Fx form functions](https://learn.microsoft.com/en-us/power-platform/power-fx/reference/function-form)
- [Power Fx Filter and delegation](https://learn.microsoft.com/en-us/power-platform/power-fx/reference/function-filter-lookup)
- [Power Fx User function](https://learn.microsoft.com/en-us/power-platform/power-fx/reference/function-user)
- [Modern Text input](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/modern-controls/modern-control-text-input)
- [PnP.PowerShell installation](https://pnp.github.io/powershell/articles/installation.html)
- [Add-PnPField](https://pnp.github.io/powershell/cmdlets/Add-PnPField.html)
- [New-PnPList](https://pnp.github.io/powershell/cmdlets/New-PnPList.html)
- [Set-PnPField](https://pnp.github.io/powershell/cmdlets/Set-PnPField.html)
- [PnP authentication](https://pnp.github.io/powershell/articles/authentication.html)
