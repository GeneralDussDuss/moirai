---
name: wrap
description: Wrap up the session before /clear - rewrite the project's thread file (goal, done, in progress, next, decisions, gotchas, open questions), save durable knowledge to CLAUDE.md and memory, flag loose ends, then confirm it is safe to clear.
argument-hint: "[anything to emphasise]"
disable-model-invocation: true
---

The user is about to `/clear` (or stop for the day). Everything not written down is about
to be forgotten, so save what a fresh session will need, and only that.

## 1. Rewrite the thread

The thread is a small handoff file that the next session loads automatically.

Find it: run `"${CLAUDE_PLUGIN_ROOT}/bin/clotho" path` and read that file if it exists
(it may hold earlier sections and an auto "Where it stopped" breadcrumb block between
`<!-- clotho:breadcrumb -->` markers).

Rewrite it **in full** with these sections, in this order, using terse bullets:

```
# Thread

## Goal
One or two lines: what the work is for and what "done" means.

## Done
Finished things worth knowing about (newest last). Merge or drop trivia.

## In progress
What is half-finished right now, with file paths and the exact state.

## Next
The concrete next step(s), in order. The first one should be startable cold.

## Decisions
- Decision: why (and what was rejected, if that will save a re-debate).

## Gotchas
Traps that cost time: commands that must be run a certain way, flaky things, wrong turns.

## Open questions
Things that need the user or more information.
```

Rules:
- Carry forward still-true items from the old thread; delete what is finished, obsolete
  or derivable from the code or git history. Never just append.
- Stay under about 55 lines in total. Omit a section's body rather than padding it
  (leave the heading with `-`), and keep each bullet to one line where you can.
- Be specific: paths, commands, names, error messages. No narration of the conversation.
- Preserve the breadcrumb block if one exists; the hooks refresh it and you must not
  edit it. If there is none, do not add one.
- No secrets, tokens or personal data: the file may sit inside a repository.

Write the file, then run `"${CLAUDE_PLUGIN_ROOT}/bin/clotho" enforce` so any overflow of
old Done items rolls into `thread.log.md`.

## 2. Save durable knowledge elsewhere

Review the session for what is durable and non-obvious beyond this one thread:
- Working knowledge for the project (how to build and test it, conventions, gotchas that
  will outlive this task) goes in that project's `CLAUDE.md`. Update existing sections
  rather than appending duplicates, and keep it tight.
- Facts about the user, their preferences and feedback, cross-project work and pointers go
  in memory, if memory is available in this setup. Check for an existing entry first and
  update it; one fact per file; index new files in `MEMORY.md`.
- Skip anything already recorded, derivable from the code or git history, or relevant only
  to this conversation. The thread is for the state of the work; CLAUDE.md and memory are
  for lasting knowledge.

## 3. Check for loose ends

In the repos touched this session: uncommitted changes, unpushed commits, background
processes still running, temporary changes to config or the environment that were not
restored. Report them; don't commit, push or clean up unless the user already asked.

## 4. Reply briefly

What you saved and where (one line each), any loose ends, and the next step. End with
"Ready to /clear." If nothing needed saving, say so in one line.

$ARGUMENTS
