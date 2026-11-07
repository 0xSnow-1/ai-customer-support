# Failures

A running log of customer-facing failures. Each entry states what the customer saw, the root cause, the evidence, and the fix.

| Date | Failure | Status |
| --- | --- | --- |
| 2026-11-07 | Customer replies cut off at the first inch mark | Fix implemented, eval run pending |

## 2026-11-07 - Customer replies cut off at the first inch mark

### What the customer saw

A customer asked which board suits a 90 kg rider. Gmail received a bare fragment.

`Ahmed, at 90 kg you would need the 11' all-round (up to 100kg) or the 12'6`

The text stopped at the first board size. The email had no complete sentence after it, no greeting line, and no sign-off.

### Root cause

The agent returns one free-form `reply` string inside an `AgentReply` JSON object. The agent model is `nvidia:nvidia/nemotron-3-ultra-550b-a55b`. The NVIDIA OpenAI-compatible endpoint decodes that JSON and treats the straight `"` in a board size such as `10'6"` as the end of the string. The rest of the reply is dropped before pydantic-ai validates it.

The provider decodes `reason` the same way. In the stored runs, both `reply` and `reason` stop at `10'6`. A token limit would not cut two fields at the same token.

Brand and tone already asks for a greeting and the `Harbor & Pine support` sign-off. The truncation removes the tail, so the customer sees a fragment that looks informal.

### Evidence

Stored eval runs show the pattern.

| Run | Case | Reply tail |
| --- | --- | --- |
| `2026-11-06T01-15-00` | `board-size-90kg` | `...between our 10'6` |
| `2026-11-06T01-15-00` | `board-size-german` | `...passt dir das 10'6` |
| `2026-11-06T01-15-00` | `pump-missing-no-order` | `...size you received (10'6` |
| `2026-11-06T01-27-22` | `board-size-90kg` | `...limit of the 10'6` |
| `2026-11-06T01-27-22` | `pump-missing-no-order` | `...size you received (10'6` |
| `2026-11-06T01-27-22` | `board-size-german` | Complete, with the sign-off |

The 01-27 German case used a curly quote instead of a straight `"` and completed. The failure follows the character, not the language.

### Why the eval missed it

`evals/run_evals.py` checked only `SectionMatches` and `ActionMatches`. The 01-27 run scored 100.0% while two customer replies were truncated. A cut email still passed both checks.

### Fix

Three changes in one branch.

1. The agent instructions and `knowledge_base/brand-and-tone.md` now ask for a greeting line, a blank line, and the sign-off. They also require feet and inches as `10 ft 6 in`, never with a double-quote mark.
2. `check_reply` in `app/ai/agent.py` rejects a reply that does not end with `Harbor & Pine support`. A truncated reply now retries instead of being sent.
3. `evals/run_evals.py` adds `ReplyEndsWithSignOff`. Every decision reply, including an escalation acknowledgement, must end with the sign-off.

### Verification

The eval has not run yet. The operator runs it.

```bash
uv run python -m evals.run_evals
```

A good run keeps the section and action score at 100.0% and adds a pass for `ReplyEndsWithSignOff` on every case.

The deployed knowledge base needs the new text before the live agent reads it.

```bash
uv run python -m scripts.seed_knowledge_base
```

### Follow-up

If a reply still truncates after the notation rule lands, switch `AGENT_MODEL` to a provider that handles JSON string escaping reliably. The Anthropic path already exists in `app/ai/models.py`.
