---
name: log
description: Show what Cerberus has recently caught - denied or asked commands and prompt-injection notes - with the rule that fired.
argument-hint: "[-n N] [--errors]"
model: sonnet
effort: low
disable-model-invocation: true
---

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/cerberus-log" $ARGUMENTS
```

Summarise in a few lines: how many catches, which rules fire most, and anything that looks
like a false positive worth allowlisting (name the config key). Secrets are redacted in the
log. `--errors` shows internal hook errors (the hooks fail open and never block the session).
