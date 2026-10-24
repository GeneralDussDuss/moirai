---
name: check
description: Dry-run Cerberus on a command (or a URL or pasted web content) without running it, and explain which head would object and why - egress, ruin or siren - and how to allowlist it if it is intended.
argument-hint: <command to test>
model: sonnet
effort: low
disable-model-invocation: true
---

Dry-run the Cerberus heads on the text below. Nothing is executed and nothing is logged.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/cerberus-check" <<'CERBERUS_INPUT_END'
$ARGUMENTS
CERBERUS_INPUT_END
```

Then explain the verdict in two or three lines:

1. Which head objected (egress, ruin) and the exact rule, or that nothing objects.
2. Whether it would be `deny` (secret literal) or `ask` (shape that needs a human), per the
   current config.
3. If the user says the command is intended, show the narrowest allowlist entry for
   `~/.config/cerberus/config.json` (`allow.hosts`, `allow.paths`, `allow.commands`,
   `allow.secrets`, or `disabled_rules`). Offer the edit; do not make it unless asked.

To test fetched web content for prompt injection instead, pipe the text to
`"${CLAUDE_PLUGIN_ROOT}/bin/cerberus-check" --siren --source <label>`.
