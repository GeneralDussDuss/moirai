# Aletheia

Nothing hidden in Claude's claims. A Claude Code plugin whose Stop hook reads Claude's final
reply, finds claims like "all tests pass" or "committed", and checks them against what
actually ran in the turn. No evidence, no stop: Claude is sent back to run it or to say it's
unverified.

```
Claude:  Fixed. All 12 tests pass.
Aletheia:   you said "All 12 tests pass." but the last test run came before your last edit (app.py).
         Run it now, or say plainly that it is unverified.
```

The turn is everything since your last real prompt. The check runs once per stop and never
blocks twice in a row (`stop_hook_active`), so it cannot loop. False positives are treated as
worse than misses: when in doubt, Aletheia stays quiet.

## What it catches

| Claim | Needs, in this turn | Blocks when |
|---|---|---|
| "tests pass", "all green", "14 tests passed" | a test-runner command (pytest, npm/pnpm/yarn/bun test, cargo/go/dotnet/mix/swift test, make test/check, vitest, jest, ctest, tox, `tests/run`, ...) after the last code edit | none ran, it ran before the last edit (stale), or it exited with an error |
| "builds clean", "compiles", "no type errors", "lint clean" | a build, lint, typecheck or test command after the last code edit | same three cases |
| "committed", "pushed to origin", "opened a PR" | `git commit`, `git push`, `gh pr create` that did not error (dry runs do not count) | none ran or it errored |
| "fixed", "works now", "I verified" | anything executed (a script, a test, an MCP tool) | you edited code and ran nothing at all |

Not claims: negations and hedges ("not tested", "haven't run", "untested", "should pass",
"once tests pass", questions), text in code blocks, inline code, quotes and blockquotes, and
past references ("already committed", "earlier all tests passed").

Stays quiet when: the turn delegated to a subagent (Aletheia cannot see inside), the only edits
were docs (`.md .txt .rst`) or files under `.claude/`, or the reply discusses failures
("2 unrelated failures").

## Audit

`/aletheia:audit [transcript.jsonl] [--last N] [--all [--days N]] [--json]` lists every claim in a
transcript with its status (OK, STALE, FAILED, MISSING, SKIPPED). With no path it scans the
newest transcript of the current project. It is read-only; the script also runs standalone:
`bin/aletheia-audit --all --days 7`.

## Install

```
/plugin marketplace add <path-or-repo-of-the-moirai-pack>
/plugin install aletheia@moirai
```

## Config

Optional `~/.config/aletheia/config.json`; every key may be omitted.

| Key | Default | Meaning |
|---|---|---|
| `enabled` | `true` | Master switch. |
| `checks` | all `true` | Per-check switches: `tests`, `build`, `vcs`, `verify` (the soft "fixed/works" check). |
| `extra_test_commands` | `[]` | Regexes; a Bash command matching one counts as a test run. |
| `extra_build_commands` | `[]` | Same for build/lint/typecheck. |
| `ignore_projects` | `[]` | Skip when the session cwd contains any of these substrings. |
| `max_blocks_per_session` | `5` | After this many blocks in one session Aletheia stops blocking. |
| `log` | `true` | Log blocks and internal errors to `~/.local/state/aletheia/aletheia.log`. |

Any internal error exits 0 silently, so Aletheia can never break a session.

## Limits

- Evidence is judged from the command line and the tool's error flag, not the output: a
  `pytest | tail` that hides a failing exit code counts as a run.
- Files written through Bash (`cat > file`, `sed -i`) are not seen as edits, so they cannot
  make an earlier test run stale.
- Only the final text after the last tool call is checked, and only claims phrased in the
  patterns above. It catches the common lies, not every one.

## Tests

`tests/run` feeds fixture transcripts and hook JSON to the hook and asserts block or allow.
