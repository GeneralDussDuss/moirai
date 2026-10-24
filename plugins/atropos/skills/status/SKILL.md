---
name: status
description: Show Atropos counters for this session - repeated calls, failing commands, subagents this turn, context size and estimated cost against the cap.
model: haiku
effort: low
disable-model-invocation: true
---

Run this and show the output to the user as is, then add at most one sentence if something
is close to a limit:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/atropos" status --session "${CLAUDE_SESSION_ID}"
```

Costs are list-price estimates, not a bill.
