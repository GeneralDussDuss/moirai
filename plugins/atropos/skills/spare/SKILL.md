---
name: spare
description: Spare this session from Atropos - reset the loop, failure, subagent and context counters, or raise/remove the budget cap for this session only.
argument-hint: "[--cap USD|off]"
model: haiku
effort: low
disable-model-invocation: true
---

The user wants Atropos to back off for this session. Run:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/atropos" spare --session "${CLAUDE_SESSION_ID}" $ARGUMENTS
```

With no arguments it clears the counters and re-arms the context warnings. `--cap 50` sets
this session's budget cap to $50, `--cap off` removes it. Report what it printed in one line.
Do not edit the user's config file.
