# Atropos

The Fate who cuts the thread. Atropos stops runaway Claude Code sessions: loops, failing
commands on repeat, subagent swarms, ballooning context and blown budgets.

## What it catches

| Problem | What happens |
|---|---|
| Same tool, identical input, again and again | Warning at 3 repeats, tool call denied at 5 (within the last 40 calls) |
| Same Bash command failing | After 2 failures the 3rd identical attempt is denied; Claude is told to diagnose or ask you |
| Subagent overspawn | More than 4 Agent/Task calls in one user turn: warning. More than 8: you are asked |
| Context bloat | One-time warning at 200k and again at 400k tokens, suggesting `/compact` or wrapping up |
| Budget cap (off by default) | Over the cap, every tool call asks first, showing the estimated spend |

Everything is a hook: fast, stdlib-only Python, and it never breaks the session. Internal
errors exit silently and are logged to `~/.local/state/atropos/errors.log`.

## Install

```
/plugin marketplace add <path-or-repo>
/plugin install atropos@moirai
```

## Commands

- `/atropos:status` shows this session's counters, context size and estimated cost.
- `/atropos:spare` resets the counters and re-arms the context warnings.
  `/atropos:spare --cap 50` sets this session's cap to $50; `--cap off` removes it.

## Config

Optional file `~/.config/atropos/config.json`. Every key is optional.

| Key | Default | Meaning |
|---|---|---|
| `enabled` | `true` | Master switch |
| `loop_warn` | `3` | Identical calls before warning |
| `loop_deny` | `5` | Identical calls before denying |
| `loop_window` | `40` | Only the last N tool calls are counted |
| `loop_ignore` | task and todo tools | Tools never counted as loops |
| `bash_fail_deny` | `3` | The Nth identical Bash attempt is denied once N-1 have failed |
| `agent_warn` | `4` | Subagents per turn before warning |
| `agent_ask` | `8` | Subagents per turn before asking |
| `context_warn` | `[200000, 400000]` | Token thresholds for the one-time warning |
| `budget_cap_usd` | `null` | Estimated session cost cap; `null` = off |
| `prices` | `{}` | Per-million-token overrides, `{"opus": [input, output, cache_read]}` for `fable`, `opus`, `sonnet`, `haiku` |

## Notes

- Cost is a list-price **estimate** from transcript token usage (main thread plus
  subagents), using a price table in `bin/atropos`. On a subscription it shows where plan
  headroom goes, not a bill. Override prices in the config if they drift.
- Context size is input + cache read + cache creation tokens of the latest assistant message.
- After you approve a budget ask, Atropos asks again only once spend grows another 25% of the cap.
- State lives in `~/.local/state/atropos/<session_id>.json`.
- Tests: `tests/run`.

MIT
