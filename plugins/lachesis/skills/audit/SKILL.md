---
name: audit
description: Audit how this machine's Claude Code sessions spend model usage - cost by model, what Opus/Fable steps actually did, context weight, and work that cheaper helpers could have done - then suggest tuning for the Lachesis routing policy.
argument-hint: "[--days N] [--project TEXT]"
model: sonnet
effort: medium
---

Run the audit and explain it plainly:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/lachesis-audit" $ARGUMENTS
```

Then tell the user, in a short plain-language summary:

1. Where usage goes: the share on Opus/Fable, and how much is context re-reading and
   writing versus actual output.
2. The biggest avoidable costs: delegable runs (name the top two or three by the prompt
   that started them), heavy-context sessions, and quick turns that could have used
   `/lachesis:quick`.
3. One to three concrete adjustments, either to how the user works (start a fresh session
   per project, `/compact` at breaks, `/lachesis:quick` for lookups) or to the routing
   policy in `${CLAUDE_PLUGIN_ROOT}/policy.md`. Propose policy edits; don't make them unless
   asked.

Costs are list-price estimates for comparing models. On a subscription they show where
plan headroom goes, not a bill; say so once. To compare before and after a change, run it
again with `--days`.
