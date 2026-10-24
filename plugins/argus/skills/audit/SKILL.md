---
name: audit
description: Scan a Claude Code transcript (the current session by default, or a given path) and list every claim like "tests pass", "builds clean", "committed" or "fixed" with its evidence status - supported, stale, failed or missing.
argument-hint: "[transcript.jsonl] [--last N] [--all [--days N]] [--json]"
model: sonnet
effort: low
---

Run the scan and report it plainly:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/argus-audit" $ARGUMENTS
```

Then tell the user, briefly:

1. How many claims were checked and how many lacked evidence.
2. For each unsupported one: the claim, what evidence was missing (no run, run before the
   last edit, run that errored), and the prompt it came from.
3. If any look like false positives (for example the evidence ran through a tool Argus
   does not know), say so and suggest an entry for `extra_test_commands` or
   `extra_build_commands` in `~/.config/argus/config.json`.

Do not re-run tests or fix anything unless asked; this is a read-only report.
