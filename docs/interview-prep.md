# Interview preparation

Adapt these answers to what you actually built and tested. Replace general statements with your screenshots, test IDs, run evidence, and lessons learned; never claim the real-AI path ran if you only used simulated mode.

## 1. What customer problem does this solve?

It gives employees one structured intake route and helps a service desk prepare consistent triage information. The measurable value is less manual rewriting and faster initial review. It does not automatically resolve tickets: an agent approves or edits the proposal.

## 2. Why did you choose SharePoint rather than Dataverse?

SharePoint fits a small Microsoft 365 prototype, works with standard connectors, and lowers the licensing barrier. The trade-off is weaker relational modeling, auditing, security granularity, and application-lifecycle support. For a larger or regulated implementation I would reassess Dataverse.

## 3. Why use a create-only trigger?

`When an item is created` gives one triage run per intake and avoids a loop when the flow later updates the same row. If retriage were a requirement, I would add an explicit retriage command or carefully designed trigger conditions rather than firing on every modification.

## 4. How does the solution work end to end?

Power Apps validates and writes the source request to SharePoint. A flow gets either a simulated object or an AI-generated object, parses and validates it, stores a proposal, and posts an Adaptive Card. An agent approves or edits the proposal, and the flow writes the final reviewed values back to the same item.

## 5. Why did you add simulated AI mode?

It removes AI capacity as a blocker and proves the SharePoint, flow, validation, Teams, and human-review integration with standard capabilities. It is deterministic test data, not evidence that the prompt is accurate, so the card shows which mode produced the proposal.

## 6. What requires extra licensing or capacity?

SharePoint and Teams connectors are Standard. AI Builder prompt runs consume AI Builder or Copilot capacity, and availability depends on the environment and current licensing. Azure OpenAI is a Premium connector and also has Azure usage cost. Copilot Studio has separate entitlement and Copilot Credit considerations.

## 7. Why did you use AI Builder instead of Azure OpenAI?

AI Builder offers a lower-code Prompt Builder experience and generated dynamic content inside Power Automate. Azure OpenAI offers more direct model/deployment control but adds a Premium connector, Azure provisioning, security configuration, and consumption cost. The shared JSON contract keeps the downstream design provider-independent.

## 8. How do you stop malformed AI output from breaking the process?

The flow parses a four-field object, validates category and priority against allow lists, limits stored text, and puts risky actions inside a Try scope. Parsing/provider failures run a Catch scope that sets neutral values and `Needs edit`; the request never silently becomes Approved.

## 9. What if the AI invents facts in the suggested reply?

The prompt restricts the reply to the request text, but prompting alone is not a control. The reply is a draft shown to an agent, it is not sent automatically, and tests score whether it contains unsupported commitments or invented causes. Repeated failures would trigger prompt revision or disabling the real branch.

## 10. How do you handle privacy and sensitive data?

The app warns users not to enter secrets or unrelated personal data, the prototype uses fictional data, and access is restricted through Team/list permissions. A standard Teams channel is required by the connector, so the enclosing Team has narrow membership. A production version would add retention, least privilege, DLP, audit, and formal data-classification review.

## 11. Why is a human in the loop?

Category, priority, and wording affect service quality, and generative models can be wrong or overconfident. The agent sees and can edit every proposal before it is final. The design also records failure as `Needs edit` rather than hiding it or sending an unreviewed reply.

## 12. How would you measure quality?

I would run a labeled, versioned test set and measure valid-JSON rate, category accuracy, priority accuracy, and especially recall for Critical requests. I would also manually score summary factuality and reply safety. I would record the prompt/model configuration so results are reproducible and compare metrics after every prompt change.

## 13. What error handling did you design?

The flow has a Try scope and a Catch scope configured for failed, timed-out, and skipped states. It validates empty source data before the provider, rejects malformed objects, defaults invalid labels, and posts an operational alert. I also test the limitation that Catch can fail if the underlying SharePoint permission or required-field problem affects both updates.

## 14. What was the most important real-world correction during the audit?

The original design targeted a private Teams channel, but Microsoft's Teams connector documents private-channel posting as unsupported. I changed it to a standard channel inside a private-membership Team and documented the security trade-off. I also separated the strict offline JSON contract from the conservative Parse JSON runtime schema.

## 15. What would you do next for production?

I would package the app and flow in a solution, use environment variables and connection references, add a durable audit record of original versus approved values, and design requester-versus-agent permissions. Then I would add monitoring, retry/dead-letter handling, retention and DLP review, accessibility testing, prompt regression gates, and an evidence-based decision on SharePoint versus Dataverse.
