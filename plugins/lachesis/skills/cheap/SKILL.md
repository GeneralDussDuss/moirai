---
name: cheap
description: Run this one turn on Sonnet for routine, well-defined work (apply this change, run the tests and fix what's obvious, rename across files, write the boilerplate). The session's own model comes back on the next message.
argument-hint: <the task>
model: sonnet
effort: medium
disable-model-invocation: true
---

The user routed this turn to Sonnet because it's routine, well-defined work. Do it
carefully, match the existing code, verify it with a real check (build, test, or command),
and report briefly what changed and how you verified it.

If it turns out to need design decisions or tricky debugging, stop and say so in one line,
so the user can send it back to the main model.

Task: $ARGUMENTS
