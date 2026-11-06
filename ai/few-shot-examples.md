# Few-shot examples

Add these examples in Prompt Builder if the selected prompt experience supports examples. If examples must be placed in the prompt text, insert them before the runtime `<request>` block. Keep the evaluation cases in `test-set.json` separate; training-like examples and evaluation examples should not overlap.

## Example 1 — access with time pressure

Input:

```text
Title: Shared mailbox unavailable for today's support shift
Description: I joined the support rota this morning but Outlook says I do not have permission to open support@contoso.example. Another agent can cover for one hour.
```

Output:

```json
{
  "category": "Access",
  "priority": "High",
  "summary": "A support-rota member lacks shared-mailbox access needed for today's shift, with one hour of temporary cover.",
  "suggestedReply": "Thanks for explaining the access issue and current cover. We will verify the shared-mailbox authorization and contact you if approval information is missing."
}
```

Why: permission is the service to restore; a near-term shift makes a single-user block high rather than critical.

## Example 2 — hardware with workaround

Input:

```text
Title: Laptop display flickers
Description: My laptop display flickers every few minutes. An external monitor works normally, so I can continue working.
```

Output:

```json
{
  "category": "Hardware",
  "priority": "Medium",
  "summary": "One employee's laptop display flickers, while an external monitor provides a working alternative.",
  "suggestedReply": "Thanks for describing the display issue and workaround. We will review the device symptoms and contact you if additional hardware details are needed."
}
```

Why: work is degraded but an adequate workaround exists.

## Example 3 — site-wide network outage

Input:

```text
Title: Warehouse Wi-Fi down
Description: Every handheld scanner and laptop in the Hamburg warehouse lost Wi-Fi. Dispatch has stopped and there is no wired option.
```

Output:

```json
{
  "category": "Network",
  "priority": "Critical",
  "summary": "A site-wide Wi-Fi outage in the Hamburg warehouse has stopped dispatch with no wired workaround.",
  "suggestedReply": "Thanks for reporting the site-wide Wi-Fi outage and operational impact. The service desk will treat this as a critical incident and coordinate investigation."
}
```

Why: a whole site and a core operation are stopped without a workaround.

## Example 4 — routine software fulfillment

Input:

```text
Title: Install approved PDF editor
Description: Please install the approved PDF editor before my workshop next month. The browser tool works until then.
```

Output:

```json
{
  "category": "Software",
  "priority": "Low",
  "summary": "An employee requests an approved PDF editor before next month's workshop and has a browser alternative.",
  "suggestedReply": "Thanks for the installation request. We will check the approved software and device requirements and contact you if more information is needed."
}
```

Why: this is planned fulfillment with time and a working alternative.
