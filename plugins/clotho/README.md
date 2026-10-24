# Clotho

The Fate who spins the thread. Every Claude Code session starts already knowing where the
work stands, across `/clear` and compaction.

## How the thread works

Each project gets one small markdown file, the **thread**: Goal, Done, In progress, Next,
Decisions (with why), Gotchas, Open questions. Hard cap of 60 lines; when it overflows,
the oldest Done items roll into `thread.log.md` next to it.

| Piece | What it does |
|---|---|
| `/clotho:wrap` | You run it before `/clear`. Claude rewrites the thread, saves lasting knowledge to `CLAUDE.md`/memory, flags loose ends, and ends with "Ready to /clear." |
| PreCompact + SessionEnd hooks | No model involved. They refresh an auto **breadcrumb** at the bottom of the thread: files edited, last failed commands, your last two requests, uncommitted git changes, a timestamp. Only the latest breadcrumb is kept, so even a session you never wrapped leaves a trail. |
| SessionStart hook | On startup, resume, clear and compact, injects the thread as context under "Thread from 3 h ago", capped at about 1.5k tokens (Goal, In progress and Next win when space is tight). A thread older than 14 days becomes a one-line mention. |
| `/clotho:thread` | Shows the thread. `/clotho:thread edit drop the Redis decision` tweaks it. |

The hooks are mechanical, fast, and never fail your session: on any internal error they
exit 0 and log to `~/.local/state/clotho/clotho.log`.

## Install

```
/plugin marketplace add <path-or-repo>
/plugin install clotho@moirai
```

## Where the thread lives

Default: `<project root>/.claude/thread.md` (project root is the git toplevel, else the
working directory). Add it to `.gitignore` if you do not want it in the repo, or set
`"location": "state"` to keep threads in `~/.local/state/clotho/<name>-<hash>.md` so
nothing lands in your repos. Your home directory itself always uses the state location.

A new thread is only created by a hook when the session did real work (an edit or at
least two requests), so quick questions leave no litter.

## Config

Optional `~/.config/clotho/config.json`; all keys optional:

```json
{ "location": "project", "stale_days": 14, "max_lines": 60, "inject_max_tokens": 1500, "enabled": true }
```

## Tests

`tests/run` runs the hooks against fixture transcripts and hook JSON in a temp directory.
