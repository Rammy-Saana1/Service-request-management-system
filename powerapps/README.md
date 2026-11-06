# Power Apps formulas

These formulas assume an English (United States) authoring locale, where function arguments use commas and behavior statements use semicolons. Other locales may use semicolons and double semicolons instead.

## Suggested controls

| Control | Name | Important property |
|---|---|---|
| Edit form | `frmRequest` | Data source: `ServiceRequests`; mode: `FormMode.New` |
| Title input | `txtTitle` | Inside the Title data card |
| Description input | `txtDescription` | Multiline; inside the Description data card |
| Submit button | `btnSubmit` | `OnSelect`: `submit-button-onselect.powerfx` |
| Status dropdown | `ddStatus` | `Items`: `colStatusFilters` |
| Search input | `txtSearch` | Classic: `DelayOutput = true`; modern: `TriggerOutput = TriggerOutput.Delayed` |
| Requests gallery | `galRequests` | `Items`: `gallery-items.powerfx` |
| Refresh icon | `icoRefresh` | `OnSelect`: `Refresh(ServiceRequests)` |

Connect the app to the SharePoint `ServiceRequests` list. Add only Title, Description, and Requester to the intake form. Do not expose Category, Priority, AI Summary, Suggested Reply, or Status as requester-editable inputs.

The formulas use properties shared by the current classic and modern text inputs, including `.Text`. For the least ambiguous beginner build, use a classic Drop down for `ddStatus`; if you use the modern Dropdown, confirm `ddStatus.Selected.Value` in Studio before continuing.

## Property map

- `App.OnStart` → `app-onstart.powerfx`
- Intake screen `OnVisible` → `screen-onvisible.powerfx`
- `btnSubmit.OnSelect` → `submit-button-onselect.powerfx`
- `btnSubmit.DisplayMode` → `submit-button-displaymode.powerfx`
- `frmRequest.OnSuccess` and `frmRequest.OnFailure` → the two sections in `request-form-events.powerfx`
- Title card `Update` → `Trim(txtTitle.Text)`
- Description card `Update` → `Trim(txtDescription.Text)`
- Requester card `Update` → `requester-datacard-update.powerfx`
- `galRequests.Items` → `gallery-items.powerfx`

The form uses `SubmitForm`, rather than `Patch`, because it honors data-card validation and exposes `OnSuccess`, `OnFailure`, and `LastSubmit` clearly to a beginner. `varSubmitting` prevents accidental double-click submissions.

## Gallery labels

Within `galRequests`, useful label formulas are:

```powerfx
// Title
ThisItem.Title

// Category and priority handle blank fields while AI processing is underway.
Coalesce(ThisItem.Category.Value, "Pending") & " · " &
Coalesce(ThisItem.Priority.Value, "Pending")

// Status
ThisItem.Status.Value

// Created time in the viewer's local settings.
Text(ThisItem.Created, DateTimeFormat.ShortDateTime)
```

## Delegation note

The gallery uses equality on the indexed Status field, `StartsWith` on the single-line Title field, and server-side sorting. Those are more SharePoint-friendly than `Search`, searching the multi-line AI summary, or wrapping columns in `Lower`. Always watch the blue delegation warning and test with more than the app's data-row limit; connector behavior can change and complex formula additions can make an otherwise delegable query local.
