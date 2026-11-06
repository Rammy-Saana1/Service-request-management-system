# Deployment guide

This guide is written for a portfolio deployment in a development tenant, not a production rollout. Microsoft changes eligibility, product names, quotas, and licensing frequently; the links in the final section are the authority. Licensing notes were checked on 25 October 2026.

## Licensing and cost reality

There is no honest way to promise that the complete AI-enabled solution is free for every developer.

| Component | Connector / entitlement | Portfolio implication |
|---|---|---|
| SharePoint list | SharePoint connector is Standard | Power Apps for Microsoft 365 in a qualifying E5 developer sandbox can build and test apps using standard connectors. |
| Canvas app | Power Apps for Microsoft 365 for standard connectors | Suitable for this SharePoint-based app. Premium connectors or Dataverse change the requirement. |
| SharePoint-triggered flow | SharePoint connector is Standard | The non-AI automation uses standard connectivity. |
| Teams review card | Microsoft Teams connector is Standard | Requires Teams, an allowed Workflows app, and access to the target channel. |
| Simulated triage response | Built-in Data Operations **Compose** action | No AI capacity is required. This proves the integration but must not be presented as an AI evaluation. |
| AI Builder custom prompt | Capacity-based; run consumes AI Builder or Copilot Credits | Building and testing a prompt in Prompt Builder does not consume these credits, but running it from a cloud flow does. An M365 developer tenant does not guarantee runtime capacity. AI Builder trials have been discontinued. |
| Azure OpenAI alternative | Power Automate connector is Premium | Also requires an Azure OpenAI resource/deployment and paid Azure consumption. It is not the free fallback. |
| Copilot Studio intake | Separate licensing and Copilot Credit considerations | Optional only; confirm entitlement and channel requirements before building. |

Microsoft states that new customers use Copilot Credits for AI Builder capacity and that, from 1 November 2026, new or renewed eligible Power Platform/Dynamics licenses no longer receive seeded AI Builder credits. Existing credits can remain through the applicable contract term. Check the current licensing guide for your tenant rather than assuming a license includes usable prompt runs.

### Microsoft 365 Developer Program caveat

The Microsoft 365 Developer Program is free to join, but an E5 developer sandbox is available only to members who qualify through an eligible path and complete any required verification. A normal Microsoft 365 subscription does not automatically qualify. A qualifying instant sandbox currently has 25 licenses including the administrator, is for development/testing only, and can be short-lived: Microsoft describes a term of up to 90 days with renewal based on qualifying development activity. Back up app and flow packages; never use the sandbox for production or durable business data.

### Power Apps Developer Plan caveat

The free Developer Plan is for development and testing and can provide a developer environment with premium-development capabilities, subject to current terms. Published limits include 750 flow runs per month and a 2 GB database. It does not give you SharePoint or Teams service entitlement by itself. Microsoft has also announced that, starting 15 November 2026, Developer Plan signup will no longer create an unmanaged developer environment automatically. Follow the current admin-center guidance if the signup experience differs from older tutorials.

## 1. Prepare the tenant

1. Join the Microsoft 365 Developer Program and check whether the dashboard offers an E5 developer sandbox. If you do not qualify, use a tenant supplied by an employer/training program or build the non-AI artifacts locally and record the licensing blocker honestly in the portfolio.
2. Provision the sandbox if offered. Store its administrator details securely and enable multifactor authentication.
3. In the Power Platform admin center, identify a development environment in the same tenant. AI Builder requires an environment with Dataverse and is available only in supported regions. A dedicated developer environment is preferable to placing experiments in a shared default environment.
4. Confirm that the maker account can create canvas apps and flows and that the environment's data-loss-prevention policy allows SharePoint, Teams, and the chosen AI connector in the same business data group.
5. Plan to complete the first end-to-end demo with **Use simulated AI = true**. Confirm AI Builder/Copilot capacity only before enabling the optional real-AI branch.

## 2. Create the collaboration locations

1. Create a SharePoint team site named **Service Desk Lab**, or choose an existing development-only site.
2. Create a Microsoft Team named **Service Desk Lab** if the site was not created through Teams.
3. Make the Team private, add only fictional service-desk test users, and create a **standard** channel named **Triage Review**. The Teams connector cannot post messages or Adaptive Cards to private channels.
4. In Teams admin settings, ensure the **Workflows** app is allowed. The flow connection owner must be a member of the Team and able to post in the channel.

The Team membership restricts the demo audience. A standard channel is required by the connector and is visible to every Team member, so keep Team membership narrow. Real production permissions need a formal access model; a demo Team is not a security design by itself.

## 3. Provision the SharePoint list

### Install PnP PowerShell

Run PowerShell **7.4.0 or later** as your normal user. Check with `$PSVersionTable.PSVersion`:

```powershell
Install-Module PnP.PowerShell -Scope CurrentUser
```

Since September 2024, PnP PowerShell interactive login requires your own Microsoft Entra app client ID. An administrator or permitted application developer can register one:

```powershell
Register-PnPEntraIDAppForInteractiveLogin `
  -ApplicationName "PnP.ServiceRequests" `
  -Tenant "YOURTENANT.onmicrosoft.com" `
  -SharePointDelegatePermissions "AllSites.FullControl"
```

Record the returned application/client ID. Delegated permission does not make the signed-in user a site owner; the user must also have permission to create lists and fields. For a production provisioning process, narrow permissions and use governed certificate-based automation rather than a maker's interactive session.

### Run the provisioning script

From the repository root:

```powershell
.\sharepoint\provision-ServiceRequests.ps1 `
  -SiteUrl "https://YOURTENANT.sharepoint.com/sites/ServiceDeskLab" `
  -ClientId "YOUR-ENTRA-APPLICATION-CLIENT-ID"
```

Open **Site contents > ServiceRequests** and confirm the columns and choice values. The display column **Description** has internal name `RequestDescription`; flows should use the dynamic-content label where possible.

### Load sample data

The CSV uses addresses under `contoso.example`, a reserved example domain that will not match tenant users. Make a working copy, replace `RequesterEmail` with licensed sandbox users, then either:

- paste rows into **Edit in grid view**, resolving each Requester as a Person value; or
- import with a small, tenant-specific PnP script after validating every user.

Do not load the pre-labeled rows if you want them to trigger the end-to-end demo. Instead, create one fresh request containing only title, description, and requester after the flow is enabled.

## 4. Optional: create the real AI Builder prompt

Skip this section for the license-free build. The simulated branch in the flow returns the same four-field object without calling an AI service.

1. Go to Power Apps or Power Automate in the chosen environment.
2. Open **AI hub > Prompts > Build your own prompt**.
3. Name it **Service Request Triage v1**.
4. Add one Text input named `RequestText`.
5. Paste the prompt from `ai/system-prompt.md`; replace its placeholder with the actual input token using **Add content**.
6. For the repository's primary flow path, keep the prompt output as **Text** and instruct it to return JSON. Power Automate cleans and parses the generated **Text** token.
7. Add the examples from `ai/few-shot-examples.md` if the interface supports examples.
8. Test with several entries from `ai/test-set.json`. Confirm there are no code fences or extra keys.
9. Save the prompt. If you instead select AI Builder's native **JSON** output, configure it from an example in the prompt editor. The generated format cannot be replaced by pasting `ai/output-schema.json`, and the flow's output tokens will differ; adapt and retest the real-provider branch.

Prompt Builder tests do not require AI Builder/Copilot Credits according to current Microsoft guidance, but running the saved prompt from a flow consumes capacity. Region availability and throttling also apply.

## 5. Build the canvas app

1. In `make.powerapps.com`, select the development environment and create a blank tablet canvas app named **Customer Request Triage Assistant**.
2. Add a SharePoint connection and select the `ServiceRequests` list.
3. Create an **Intake** screen with an Edit form named `frmRequest` in New mode. Add only Title, Description, and Requester.
4. Rename the input controls to `txtTitle` and `txtDescription`; make description multiline.
5. Lock or hide the Requester card and use `powerapps/requester-datacard-update.powerfx` for its Update property.
6. Add a privacy hint: **Do not enter passwords, authentication codes, payment-card data, or unrelated personal information.**
7. Add a Submit button and copy the formulas according to `powerapps/README.md`.
8. Create a **Requests** screen with `ddStatus`, `txtSearch`, `galRequests`, and a refresh icon. Apply `gallery-items.powerfx` to the gallery.
9. Run `App.OnStart` from the app menu once after pasting its formula, or close and reopen the preview.
10. Test required fields, length limits, double-click prevention, success, and connector failure behavior.
11. Save and publish the app. Share it only with test users, and separately grant those users the intended SharePoint permissions; app sharing does not grant list access.

For a production app, enforce list item-level permissions or another data model so requesters cannot read other employees' requests. The portfolio prototype should be demonstrated only with fictional data and appropriately restricted test users.

## 6. Build the cloud flow

Follow `powerautomate/flow-build-guide.md` and use the exact action names shown there. Naming matters because expressions such as `outputs('Validated_Category')` are generated from action names.

Important checks:

- Start with the Boolean variable **Use simulated AI** set to `true`. In this mode, the **Simulated AI response** Compose action returns a fixed object and no AI Builder action or capacity is needed.
- Treat the Compose result as test data, not an AI result. The Teams card displays the active mode.
- When the standard-connector path passes, add **Run a prompt** in the real-provider branch, map its generated **Text** token, and change the switch to `false` for a controlled test.
- Select the list from the SharePoint connector dropdown rather than entering an ambiguous text value.
- Use the generated **Text** token from `Run a prompt`; do not guess its internal response path.
- Paste and validate `powerautomate/adaptive-card.json` in the current Teams wait-for-response action.
- Configure a replacement/update message so other agents do not try to submit an already handled card.
- Add the Catch scope and test it; a happy-path-only flow is not complete.
- Turn on the flow only after all connections are authenticated and the Team/channel selectors resolve.

## 7. End-to-end verification

Use separate requester and reviewer test accounts where practical.

1. Keep **Use simulated AI = true**, submit an item in Power Apps, and record the displayed request ID.
2. Confirm SharePoint initially records the source fields and `New` status.
3. Confirm the flow run uses **Simulated AI response**, parses the object, applies allow-list validation, and sets `Awaiting review`.
4. Confirm the card is visible only in the intended service-desk channel.
5. Choose **Approve** and confirm the proposed values remain unchanged.
6. Submit a second item, edit category or wording, choose **Edit and approve**, and confirm the edited values are stored.
7. Confirm later clicks on the handled card cannot change the item.
8. Temporarily replace the simulated Compose input with invalid JSON and confirm the Catch scope sets `Needs edit` with neutral fallback values; then restore it.
9. If capacity is available, build the real-AI branch, set **Use simulated AI = false**, and repeat the run. Confirm **Run a prompt** was called and the card says **REAL AI**.
10. Run the injection and outage cases from `ai/test-set.json` only against the real-AI branch; simulated mode cannot measure prompt quality.
11. Capture the five redacted screenshots listed in `docs/images/README.md`.

## 8. Portfolio handoff checklist

- Export the canvas app package and flow/solution for backup, but do not commit credentials, connection IDs, tenant URLs, or real request data.
- Replace tenant-specific values in screenshots and documentation with placeholders.
- Record prompt version, test date, model/configuration shown by Prompt Builder, and test results.
- Explain the premium AI boundary during the demo rather than hiding it.
- Be ready to discuss why human review, a failure path, and critical-recall measurement matter.

## Official references

- [Microsoft 365 Developer Program eligibility](https://learn.microsoft.com/en-us/office/developer-program/microsoft-365-developer-program)
- [Microsoft 365 Developer Program FAQ and sandbox lifecycle](https://learn.microsoft.com/en-us/office/developer-program/microsoft-365-developer-program-faq)
- [Build Microsoft 365 solutions with the developer subscription](https://learn.microsoft.com/en-us/office/developer-program/build-microsoft-365-solutions)
- [Power Apps Developer Plan](https://learn.microsoft.com/en-us/power-platform/developer/plan)
- [AI Builder licensing overview](https://learn.microsoft.com/en-us/ai-builder/administer-licensing)
- [AI Builder credits and prompt licensing](https://learn.microsoft.com/en-us/ai-builder/credit-management)
- [Use a custom prompt in Power Automate](https://learn.microsoft.com/en-us/ai-builder/use-a-custom-prompt-in-flow)
- [SharePoint connector classification](https://learn.microsoft.com/en-us/connectors/sharepointonline/)
- [Microsoft Teams connector classification and limits](https://learn.microsoft.com/en-us/connectors/teams/)
- [Adaptive Cards in Power Automate](https://learn.microsoft.com/en-us/power-automate/overview-adaptive-cards)
- [JSON output for prompts](https://learn.microsoft.com/en-us/microsoft-copilot-studio/process-responses-json-output)
- [Azure OpenAI connector classification](https://learn.microsoft.com/en-us/connectors/azureopenai/)
- [PnP PowerShell installation requirements](https://pnp.github.io/powershell/articles/installation.html)
- [PnP PowerShell application registration](https://pnp.github.io/powershell/articles/registerapplication.html)
