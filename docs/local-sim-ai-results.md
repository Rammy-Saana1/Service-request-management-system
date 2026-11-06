# Local simulation AI results

The local classifier is deterministic and uses no paid service or network connection. Category and priority are each counted as one label. Exact-case accuracy requires both labels in a case to match.

## Before the priority-rule change

The original rules were evaluated with:

```text
python .\local-sim\evaluate_ai.py
```

| Measure | Result |
|---|---:|
| Category accuracy | 8/8 (100.0%) |
| Priority accuracy | 2/8 (25.0%) |
| Overall label accuracy | 10/16 (62.5%) |
| Exact-case accuracy | 2/8 (25.0%) |

Six priorities defaulted to Medium because the rules depended on a small set of exact phrases. See `docs/priority-miss-analysis.md` for the case-by-case baseline analysis.

## What changed

Priority now uses separate, explainable signals and applies them in this order:

1. Severe security or safety risk, a widespread outage, or a stopped operation with no workaround is Critical.
2. A credible security warning, or blocked work with no workaround plus a near deadline or multiple affected users, is High.
3. A strong workaround for a small issue, or clearly planned, distant, cosmetic, or optional work, is Low.
4. Missing, mixed, or ambiguous evidence remains Medium.

An urgency word, requested label, or requester job title is not enough to raise priority. The category rules were not changed, and every proposal still requires manager review.

## After the change: original eight cases (tuned on this set)

| Case | Expected priority | Actual priority | Result |
|---|---|---|---|
| T01 | Medium | Medium | Pass |
| T02 | Critical | Critical | Pass |
| T03 | Low | Low | Pass |
| T04 | High | High | Pass |
| T05 | Low | Low | Pass |
| T06 | Medium | Medium | Pass |
| T07 | Low | Low | Pass |
| T08 | Low | Low | Pass |

| Measure | Result |
|---|---:|
| Category accuracy | 8/8 (100.0%) |
| Priority accuracy | 8/8 (100.0%) |
| Overall label accuracy | 16/16 (100.0%) |
| Exact-case accuracy | 8/8 (100.0%) |

## One-time held-out evaluation (one-time, unseen)

The rules and regression tests were finalized before this command was run:

```text
python .\local-sim\evaluate_ai.py --test-set .\ai\holdout-cases.json
```

The holdout was run once and the rules were not tuned afterward.

| Case | Expected category | Actual category | Expected priority | Actual priority | Result |
|---|---|---|---|---|---|
| H01 | Access | Access | High | High | Pass |
| H02 | Hardware | Hardware | Low | Low | Pass |
| H03 | Software | Software | Critical | Critical | Pass |
| H04 | Network | Network | High | Medium | **Priority fail** |
| H05 | Microsoft 365 | Microsoft 365 | Low | Medium | **Priority fail** |
| H06 | Software | Software | Medium | Medium | Pass |
| H07 | Access | Access | Low | Low | Pass |
| H08 | Network | Network | Medium | Medium | Pass |

| Measure | Result |
|---|---:|
| Category accuracy | 8/8 (100.0%) |
| Priority accuracy | 6/8 (75.0%) |
| Overall label accuracy | 14/16 (87.5%) |
| Exact-case accuracy | 6/8 (75.0%) |

**Known limitations at the time of the unseen run:** H04 missed number-word deadlines such as “two hours,” and H05 misread negation in “Nothing is blocked today.”

## Post-analysis regression rerun (not unseen)

The two known language gaps were then added as general regression cases. Number words from one through twelve are now recognized for hour/minute deadlines, and explicit phrases that negate current impact no longer activate the `today` urgency signal. Because these changes were informed by H04 and H05, this rerun is a regression check, not a new generalization measurement.

| Measure | Result |
|---|---:|
| Category accuracy | 8/8 (100.0%) |
| Priority accuracy | 8/8 (100.0%) |
| Overall label accuracy | 16/16 (100.0%) |
| Exact-case accuracy | 8/8 (100.0%) |

## False-positive follow-up

Final QA found three new false-positive patterns: a negated outage, planned future maintenance with a backup, and routine phishing training. The priority rules now:

- remove a small allow-list of explicitly negated incident phrases before testing risk and outage signals;
- treat planned maintenance as non-active unless the text also describes a current outage or stopped operation; and
- separate routine security training, exercises, simulations, and drills from active security evidence such as a clicked phishing link or suspicious sign-in.

Each reassuring case has an urgent counterpart to make sure the suppression does not hide a real incident:

| Regression case | Expected | Actual |
|---|---:|---:|
| Internet is not down; nobody is blocked | Low | Low |
| Internet is down now for all employees with no workaround | Critical | Critical |
| Planned outage next week with a backup connection | Low | Low |
| Maintenance overrun with a current company outage | Critical | Critical |
| Routine phishing-awareness training next month | Low | Low |
| Clicked phishing link followed by suspicious sign-in | High | High |

After this change, the complete automated suite passed **37/37**. The original tuned set and the holdout regression set both remained 8/8 for category, 8/8 for priority, 16/16 for labels, and 8/8 for exact cases. The holdout has already informed earlier rule changes, so its current score is regression evidence rather than an unseen generalization result.

## Remaining limitations

- The classifier matches explainable text patterns; it does not understand language like a model. Negation and planned/routine context are recognized only through listed phrases, so unfamiliar wording, spelling, long sentences, and conflicting statements can still cause errors.
- A request can omit important impact or workaround details. Such cases deliberately default to Medium rather than guessing.
- Both eight-case sets are small. The 100% regression scores do not establish accuracy on real service-desk language.
- The local proposal never bypasses human review. A manager can edit the suggested priority before approving or rejecting the request.
