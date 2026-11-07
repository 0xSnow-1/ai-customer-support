# Evaluation Results

The golden set contains 18 customer emails.
The first prompt-tuning runs below used two binary checks per case: the section and the action.
A perfect score for those runs was 36 of 36 checks, reported as 100.0% assertions.

The suite now checks four things per case: the section, the action, the sign-off, and plain text.
See `evals/run_evals.py` and the README for the current checks.
The 2026-11-07 runs are not listed here yet.

## Run history

| Run | Assertions | Notes |
| --- | --- | --- |
| 2026-11-05T22-09-14 | 97.2% | Baseline. `pump-missing-no-order` escalated instead of replying. |
| 2026-11-06T01-15-00 | 94.4% | First prompt change. Fixed the pump case, exposed two flaky cases. |
| 2026-11-06T01-27-22 | 100.0% | Final prompts. All 36 checks pass. |

Each run is stored next to this file in `evals/runs/` as a JSON record and a console transcript.
The baseline is transcript only because run saving was added afterwards.

## Root causes

### Agent: covered problem treated as a knowledge base gap

`pump-missing-no-order` asked about a missing pump with no order number.
The knowledge base covers this case: a missing accessory is shipped without a return, and the order number is needed to arrange it.
The agent set `enough_information=False`, which `decide.py:29` turns into an escalation.
The prompt did not separate "the knowledge base has no answer" from "the customer has not supplied the details needed to act".

Fix: `app/ai/agent.py:20` now defines `enough_information` as a property of the knowledge base, not of the customer.
It stays true when the topic is covered, even if the reply must ask for order number, model, board size, or a photo.

This also fixed a flaky `slow-leak-first-contact` failure with the same cause.

### Classifier: wrong item routed as shipping or returns

`wrong-finish` was classified as `shelving`, `shipping`, or `returns-and-warranty` across samples.
"Wrong color" reads like a delivery error or a return, but the shelving section owns finishes and exchanges.

Fix: `app/ai/classifier.py:18` adds a general routing rule.
A wrong, missing, or damaged item belongs to the product's section, shipping handles delivery status and replacement parts, and returns-and-warranty handles refund and return requests.

## Verification

After the prompt changes, each flaky path was sampled five times:

- `wrong-finish` classified as `shelving` in 5 of 5 samples.
- `slow-leak-first-contact` returned `action=reply, enough_information=True` in 5 of 5 samples.
- `pump-missing-no-order` returned `action=reply, enough_information=True` in 5 of 5 samples.

A full run then scored 100.0%.

## Reproduce

```bash
uv run python -m evals.run_evals
```

Runs are written to `evals/runs/<timestamp>-golden-emails.json` and `.txt`.
