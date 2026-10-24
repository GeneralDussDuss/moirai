---
name: quick
description: Run this one turn on Haiku for a quick lookup or small task (what's my IP, which package owns this file, convert this, a one-liner). The session's own model comes back on the next message.
argument-hint: <what you want>
model: haiku
effort: low
disable-model-invocation: true
---

The user sent this as a quick request, deliberately routed to a fast, cheap model for this
one turn. Do it directly with as few tool calls as possible, and answer in a few lines.

If it turns out to need real design, debugging judgment or more than a handful of steps,
don't push through: say in one line that it deserves the main model and that the next
message will run on it.

Request: $ARGUMENTS
