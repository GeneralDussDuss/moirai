## Lachesis: model routing

Most of a session's cost is the main conversation re-reading its own context on every
step, not thinking. A small step in a 300k-token conversation costs as much as a page of
output. Spend the main model on judgment and send the rest to cheaper helpers.

**Keep on the main model:** planning, architecture, design and visual taste, debugging
judgment, anything that hinges on nuance from this conversation, and every final answer.

**Hand to `lachesis:scout` (Haiku, read-only)** when answering a question would take 3+
reads: finding where something lives, reading logs, docs or many files, inventories, web
lookups. Ask it a specific question and for a short answer with `file:line` references.

**Hand to `lachesis:worker` (Sonnet)** well-specified multi-step execution: applying a
written plan, mechanical edits across files, a build/test/fix loop, repetitive verification
(restart, check status, measure, tweak). Brief it in a few lines and include the check that
proves it's done. It reports what it changed and the check's result.

**Don't delegate** anything under ~3 tool calls, work that's hard to brief without this
conversation's context, or anything destructive or outward-facing. A bad hand-off costs more
than it saves.

**Keep the main context lean.** Every step re-sends the whole conversation, so cost is
roughly context size x number of steps. A fresh session starts near 40k; long ones can
reach several hundred k.

- *Fewer steps:* batch independent tool calls into one step (parallel calls, or several
  commands in one shell call) instead of one look per step.
- *Smaller results:* trim output (`head`, `tail`, `grep -c`, `--stat`), read the slice you
  need rather than the whole file, and shrink or crop screenshots before viewing (about
  1000px wide is plenty; a contact sheet beats many separate frames).
- *Reading stays outside:* exploration that's mostly reading goes to the scout, so only its
  answer enters this conversation. Big reference material (API docs, long skill references)
  is also best loaded by a helper that returns just the needed facts.
- *Session hygiene:* when the user moves to an unrelated task, suggest `/clear` (one line,
  once), and `/clotho:wrap` first if Clotho is installed, so a fresh session knows where
  things stand. Partway through one long task, past ~200k, suggest `/compact` at a natural
  break.
