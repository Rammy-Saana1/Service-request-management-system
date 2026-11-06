# AI assets

- `system-prompt.md` is the deployable prompt and setup note.
- `few-shot-examples.md` contains examples that teach boundary cases.
- `output-schema.json` is the expected contract for documentation and offline validation.
- `test-set.json` is held-out evaluation data with expected outputs.

Exact generated wording can vary even when labels are correct. Score category and priority automatically, then have a human judge whether summaries are fully supported and replies contain no invented claims. Do not change expected outputs merely to match a weak model run; document and analyze disagreements.

`output-schema.json` is the strict contract used for offline validation. The flow uses the simpler `powerautomate/parse-json-schema.json`, then performs category and priority allow-list checks itself. This lets an unexpected label reach the safe fallback instead of relying on undocumented Parse JSON draft support.
