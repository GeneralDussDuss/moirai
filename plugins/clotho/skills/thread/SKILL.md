---
name: thread
description: Show this project's Clotho thread (the handoff file new sessions start with), or change it with "edit <instruction>".
argument-hint: "[edit <instruction>]"
disable-model-invocation: true
---

The thread is this project's handoff file. Locate it with
`"${CLAUDE_PLUGIN_ROOT}/bin/clotho" path`.

Arguments: `$ARGUMENTS`

- **No arguments**: print the thread file verbatim (run `"${CLAUDE_PLUGIN_ROOT}/bin/clotho" show`),
  then one line saying where it lives and how old it is. If there is no thread yet, say so
  and suggest `/clotho:wrap`.
- **`edit <instruction>`**: apply the instruction to the thread file (for example "drop the
  Redis decision", "next step is the migration", "add a gotcha about the flaky test").
  Make the smallest edit that does it, keep the section layout, do not touch the
  `<!-- clotho:breadcrumb -->` block, keep the file under about 60 lines, then run
  `"${CLAUDE_PLUGIN_ROOT}/bin/clotho" enforce` and show the changed section.
  If the file does not exist, create it with the standard sections (Goal, Done, In progress,
  Next, Decisions, Gotchas, Open questions) first.
- Anything else: treat it as a question about the thread and answer from its contents.
