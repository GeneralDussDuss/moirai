"""Argus core: parse a Claude Code transcript into turns, find claims in the
final assistant text, and check each against the tool calls of that turn.

Stdlib only. Imported by argus-stop (hook) and argus-audit (CLI).
"""
import json
import os
import re
import shlex
import time

HOME = os.path.expanduser("~")
CONFIG_PATH = os.path.join(HOME, ".config", "argus", "config.json")
STATE_DIR = os.path.join(HOME, ".local", "state", "argus")

DEFAULT_CONFIG = {
    "enabled": True,
    "checks": {"tests": True, "build": True, "vcs": True, "verify": True},
    "extra_test_commands": [],     # regexes searched in the Bash command
    "extra_build_commands": [],
    "ignore_projects": [],         # skip when cwd contains any of these substrings
    "max_blocks_per_session": 5,   # safety valve against nagging
    "log": True,
}


def load_config():
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        with open(CONFIG_PATH) as f:
            user = json.load(f)
        for k, v in user.items():
            if k == "checks" and isinstance(v, dict):
                cfg["checks"].update({a: bool(b) for a, b in v.items()})
            elif k in cfg and k != "checks":
                cfg[k] = v
    except Exception:
        pass
    return cfg


def log(msg, cfg=None):
    try:
        if cfg is not None and not cfg.get("log", True):
            return
        os.makedirs(STATE_DIR, exist_ok=True)
        p = os.path.join(STATE_DIR, "argus.log")
        if os.path.exists(p) and os.path.getsize(p) > 200_000:
            os.replace(p, p + ".1")
        with open(p, "a") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------- transcript

NOT_PROMPT_PREFIXES = (
    "<local-command-", "<task-notification", "<system-reminder", "Stop hook feedback",
    "[Request interrupted", "<bash-", "Caveat:",
)
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
DELEGATE_TOOLS = {"Agent", "Task", "Workflow", "SendMessage"}
# Edits to these never invalidate a test/build run.
DOC_EXT = (".md", ".txt", ".rst", ".adoc")


def read_entries(path, tail_bytes=None):
    """Parse a JSONL transcript. With tail_bytes, only the end of the file
    (a partial first line is dropped)."""
    with open(path, "rb") as f:
        size = os.fstat(f.fileno()).st_size
        partial = False
        if tail_bytes and size > tail_bytes:
            f.seek(size - tail_bytes)
            partial = True
        data = f.read()
    lines = data.split(b"\n")
    if partial:
        lines = lines[1:]
    out = []
    for ln in lines:
        if not ln.strip():
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def _blocks(entry):
    c = (entry.get("message") or {}).get("content")
    if isinstance(c, str):
        return [{"type": "text", "text": c}]
    return [b for b in (c or []) if isinstance(b, dict)]


def is_real_prompt(e):
    if e.get("type") != "user" or e.get("isMeta") or e.get("isSidechain") or e.get("isCompactSummary"):
        return False
    blocks = _blocks(e)
    if not blocks or any(b.get("type") == "tool_result" for b in blocks):
        return False
    text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
    if not text:
        return False
    return not text.startswith(NOT_PROMPT_PREFIXES)


def prompt_text(e):
    return "".join(b.get("text", "") for b in _blocks(e) if b.get("type") == "text").strip()


def split_turns(entries):
    """List of turns: {prompt, tools:[...], final_text}. A turn starts at a real
    user prompt. Tools are in call order with result error flags attached."""
    turns, cur, by_id = [], None, {}
    for e in entries:
        if e.get("isSidechain"):
            continue
        t = e.get("type")
        if t == "user" and is_real_prompt(e):
            cur = {"prompt": prompt_text(e), "tools": [], "final_text": "", "cwd": e.get("cwd", "")}
            turns.append(cur)
            continue
        if cur is None:
            continue
        if t == "assistant":
            for b in _blocks(e):
                if b.get("type") == "tool_use":
                    tool = {"i": len(cur["tools"]), "id": b.get("id"), "name": b.get("name", ""),
                            "input": b.get("input") or {}, "err": None}
                    cur["tools"].append(tool)
                    by_id[tool["id"]] = tool
                    cur["final_text"] = ""
                elif b.get("type") == "text":
                    cur["final_text"] += ("\n" if cur["final_text"] else "") + (b.get("text") or "")
        elif t == "user":
            for b in _blocks(e):
                if b.get("type") == "tool_result":
                    tool = by_id.get(b.get("tool_use_id"))
                    if tool is not None:
                        tool["err"] = bool(b.get("is_error"))
    return turns


# ------------------------------------------------------------ command parsing

WRAPPERS = {"time", "nice", "sudo", "env", "command", "exec", "nohup", "stdbuf", "xvfb-run",
            "npx", "bunx", "pnpx", "uvx", "unbuffer", "ionice", "doas"}
RUN_PREFIX = [("uv", "run"), ("poetry", "run"), ("pipenv", "run"), ("pnpm", "exec"), ("pnpm", "dlx"),
              ("yarn", "dlx"), ("bun", "x"), ("npm", "exec"), ("rye", "run"), ("pdm", "run"), ("hatch", "run")]
SEG_SPLIT = re.compile(r"\s*(?:&&|\|\||;|\||\n|&(?!>))\s*")
ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def _tokens(seg):
    seg = seg.strip().lstrip("({").strip()
    if not seg or seg.startswith("#"):
        return []
    try:
        toks = shlex.split(seg)
    except Exception:
        toks = seg.split()
    changed = True
    while toks and changed:
        changed = False
        if ENV_ASSIGN.match(toks[0]):
            toks = toks[1:]
            changed = True
        elif toks[0] in WRAPPERS:
            toks = toks[1:]
            if toks and toks[0].isdigit():
                toks = toks[1:]
            changed = True
        elif toks[0] == "timeout" and len(toks) > 1:
            toks = toks[2:]
            changed = True
        else:
            for a, b in RUN_PREFIX:
                if len(toks) > 1 and toks[0] == a and toks[1] == b:
                    toks = toks[2:]
                    changed = True
                    break
    return toks


def command_segments(cmd, _depth=0):
    """Token lists, one per simple command in a shell string (bash -c recursed)."""
    out = []
    for seg in SEG_SPLIT.split(cmd or ""):
        toks = _tokens(seg)
        if not toks:
            continue
        base = os.path.basename(toks[0])
        if base in ("bash", "sh", "zsh") and "-c" in toks and _depth < 3:
            i = toks.index("-c")
            if i + 1 < len(toks):
                out.extend(command_segments(toks[i + 1], _depth + 1))
                continue
        out.append(toks)
    return out


def _script_is_test(path):
    base = os.path.basename(path)
    parent = os.path.basename(os.path.dirname(path))
    if re.match(r"^(test_.*|.*_tests?|tests?|run[-_]?tests?|tests?\.(sh|py|js|ts)|check\.sh|test[-_]all.*)(\.\w+)?$", base):
        return True
    if base == "run" and parent in ("tests", "test", "t"):
        return True
    return False


def is_test_segment(toks):
    first = os.path.basename(toks[0])
    rest = toks[1:]
    r0 = rest[0] if rest else ""
    if first in {"pytest", "py.test", "tox", "nox", "vitest", "jest", "rspec", "phpunit", "ctest",
                 "bats", "nextest", "busted", "prove", "playwright-test"}:
        return True
    if first == "go" and r0 == "test":
        return True
    if first == "cargo" and r0 in ("test", "nextest", "t"):
        return True
    if first in ("npm", "pnpm", "yarn", "bun", "deno"):
        if r0 in ("test", "t", "tests"):
            return True
        if r0 in ("run", "run-script") and len(rest) > 1 and rest[1].startswith(("test", "e2e", "spec")):
            return True
    if first in ("make", "gmake", "ninja") and any(a in ("test", "tests", "check", "verify") for a in rest):
        return True
    if first in ("mvn", "mvnw", "gradle", "gradlew") and any(a in ("test", "verify", "check") for a in rest):
        return True
    if first == "dotnet" and r0 == "test":
        return True
    if first in ("mix", "swift") and r0 == "test":
        return True
    if first == "zig" and "test" in rest:
        return True
    if first == "node" and "--test" in rest:
        return True
    if first.startswith("python") or first == "py":
        if r0 == "-m" and len(rest) > 1:
            mod = rest[1]
            return mod.split(".")[0] in ("pytest", "unittest", "nose", "nose2", "tox") or "test" in mod
        for a in rest:
            if a.startswith("-"):
                continue
            return _script_is_test(a)
    if first in ("bash", "sh", "zsh", "node", "ruby", "perl", "lua", "deno", "bun") or "/" in toks[0] or toks[0].startswith("."):
        target = toks[0]
        if first in ("bash", "sh", "zsh", "node", "ruby", "perl", "lua", "deno", "bun"):
            target = next((a for a in rest if not a.startswith("-")), "")
        if target:
            return _script_is_test(target)
    return False


BUILD_TOOLS = {"tsc", "eslint", "prettier", "ruff", "flake8", "pylint", "mypy", "pyright", "black", "isort",
               "shellcheck", "shfmt", "rustc", "gcc", "g++", "cc", "c++", "clang", "clang++", "javac", "cmake",
               "meson", "luac", "makepkg", "qmllint", "biome", "oxlint", "stylelint", "golangci-lint", "hadolint",
               "ninja", "make", "gmake", "mvn", "mvnw", "gradle", "gradlew", "xcodebuild", "msbuild"}


def is_build_segment(toks):
    if is_test_segment(toks):
        return True
    first = os.path.basename(toks[0])
    rest = toks[1:]
    r0 = rest[0] if rest else ""
    if first in BUILD_TOOLS:
        return True
    if first == "cargo" and r0 in ("build", "check", "clippy", "fmt", "doc", "b", "c"):
        return True
    if first == "go" and r0 in ("build", "vet", "install"):
        return True
    if first in ("npm", "pnpm", "yarn", "bun"):
        if r0 in ("build", "lint", "typecheck", "tsc", "compile", "check"):
            return True
        if r0 in ("run", "run-script") and len(rest) > 1 and re.match(r"(build|lint|typecheck|type-check|check|compile|tsc|format:check)", rest[1]):
            return True
    if first == "dotnet" and r0 in ("build", "publish"):
        return True
    if first == "swift" and r0 == "build":
        return True
    if first == "zig" and r0 in ("build", "ast-check"):
        return True
    if first == "docker" and r0 in ("build", "buildx"):
        return True
    if first in ("bash", "sh", "zsh") and "-n" in rest:
        return True
    if first == "node" and any(a in ("--check", "-c") for a in rest):
        return True
    if first.startswith("python") or first == "py":
        if r0 == "-m" and len(rest) > 1:
            return rest[1].split(".")[0] in ("py_compile", "compileall", "mypy", "ruff", "flake8", "pylint",
                                             "black", "pyright", "isort")
    return False


def _git_sub(toks):
    """Subcommand and args of a git invocation, skipping global options."""
    if os.path.basename(toks[0]) != "git":
        return None, []
    i = 1
    while i < len(toks):
        a = toks[i]
        if a in ("-C", "-c", "--git-dir", "--work-tree", "--namespace"):
            i += 2
        elif a.startswith("-"):
            i += 1
        else:
            return a, toks[i + 1:]
    return None, []


def vcs_kinds(toks):
    """Which VCS claim kinds this simple command would satisfy."""
    first = os.path.basename(toks[0])
    kinds = set()
    if first == "git":
        sub, args = _git_sub(toks)
        dry = any(a in ("--dry-run", "-n") for a in args)
        if sub == "commit" and "--dry-run" not in args:
            kinds.add("commit")
        if sub == "push" and not dry:
            kinds.add("push")
    elif first == "jj":
        if len(toks) > 1 and toks[1] in ("commit", "describe", "new"):
            kinds.add("commit")
        if toks[1:3] == ["git", "push"]:
            kinds.add("push")
    elif first == "gh" and toks[1:3] == ["pr", "create"]:
        kinds.add("pr")
    elif first == "glab" and toks[1:3] == ["mr", "create"]:
        kinds.add("pr")
    return kinds


# Commands that do not run project code. A turn whose only Bash calls are these
# has executed nothing.
NONEXEC = {"cd", "ls", "cat", "head", "tail", "grep", "rg", "find", "fd", "wc", "stat", "file", "jq", "sort",
           "uniq", "cut", "tr", "diff", "cmp", "which", "type", "echo", "printf", "pwd", "date", "du", "df",
           "tree", "less", "readlink", "realpath", "basename", "dirname", "true", "test", "[", "mkdir", "cp",
           "mv", "rm", "touch", "chmod", "ln", "git", "sed", "awk", "column", "xxd", "od", "md5sum",
           "sha256sum", "export", "set", "ps", "env", "id", "whoami", "uname", "hostname", "tee", "gh", "jj"}


def bash_is_exec(cmd):
    for toks in command_segments(cmd):
        if os.path.basename(toks[0]) not in NONEXEC:
            return True
    return False


def is_code_edit(tool):
    if tool["name"] not in EDIT_TOOLS:
        return False
    inp = tool["input"]
    p = inp.get("file_path") or inp.get("notebook_path") or inp.get("path") or ""
    if p.lower().endswith(DOC_EXT) or "/.claude/" in p:
        return False
    return True


# -------------------------------------------------------------------- claims

def strip_quoted(text):
    text = re.sub(r"```.*?(```|\Z)", " ", text, flags=re.S)
    text = re.sub(r"~~~.*?(~~~|\Z)", " ", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = re.sub(r'"[^"\n]{0,300}"|“[^”\n]{0,300}”', " ", text)
    text = "\n".join(l for l in text.split("\n") if not l.lstrip().startswith(">"))
    return text


def sentences(text):
    out = []
    for line in strip_quoted(text).split("\n"):
        line = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", line)
        line = re.sub(r"[*_#|]+", " ", line)
        for s in re.split(r"(?<=[.!?;])\s+|\s+[-—–]{1,2}\s+|\s{2,}", line):
            s = s.strip()
            if s:
                out.append(s)
    return out


I = re.I
HEDGE = re.compile(
    r"\b(not|\w+n't|never|nothing|nobody|none|nowhere|untested|unverified|unconfirmed|unable|haven'?t|hasn'?t|hadn'?t|didn'?t|couldn'?t|can'?t|cannot|won'?t|"
    r"wouldn'?t|shouldn'?t|should|would|could|might|may|hopefully|hope|likely|probably|presumably|supposed|ought|"
    r"if|whether|unless|until|once|assuming|assume|need(?:s|ed)? to|want(?:s)?|wish|please|try|trying|let me|let'?s|"
    r"i'?ll|i will|i'?m going|going to|will|to pass|to be green|to build|to compile|make sure|ensure|"
    r"check (?:that|whether|if)|verify (?:that|whether|if)|todo|expect(?:s)? (?:it|them|this|that|the)|"
    r"expected to|so that|in order to|aim|goal|ready to|before (?:i|we|you)|after (?:you|i|we) (?:run|commit|push|merge)|"
    r"you (?:can|may|could|should)|run it|when you|next time|uncertain|unsure|not sure|"
    r"(?:make|makes|making|get|gets|getting|keep|keeps)\s+(?:\w+\s+){0,3}?(?:pass|green)|"
    r"fail(?:s|ed|ing|ure|ures)?|broke|broken)\b", I)
NO_HEDGE_KINDS = {"build"}      # "no type errors" is the claim, not a negation
NO_WORDS = re.compile(r"\b(no|without|zero)\b", I)
PAST = re.compile(r"\b(already|earlier|previously|before|last (?:time|run|turn|session)|originally|were passing|"
                  r"was passing|used to|baseline|prior|from (?:the )?(?:earlier|last|previous)|ran earlier|"
                  r"yesterday|last week|was committed|were committed|was pushed|were pushed)\b", I)
FAILWORDS = re.compile(r"\b(fail(?:s|ed|ing|ure|ures)?|pre-?existing|flaky|unrelated|error(?:s|ed)?)\b", I)

CLAIM_PATTERNS = {
    "test": [
        r"\btests\s+(?:suite\s+)?(?:(?:are|is|now|all|still|were)\s+)*(?:pass(?:ed|es|ing)?|green|succeed(?:s|ed)?)\b",
        r"\b(?:the|this|that|new|my|our|its|unit|regression|integration)\s+(?:\w+\s+)?test\s+(?:(?:is|now|still)\s+)*(?:pass(?:ed|es|ing)?|green)\b",
        r"\b(?:all|every)\s+(?:\w+\s+){0,3}?tests?\s+(?:(?:are|is|now|all)\s+)*(?:pass(?:ed|es|ing)?|green)\b",
        r"\b\d+\s*(?:/\s*\d+\s+)?(?:\w+\s+)?(?:tests?|specs?|assertions?|test cases?)\s+(?:(?:are|all|now)\s+)*(?:pass(?:ed|es|ing)?|green)\b",
        r"\btest suite\s+(?:is\s+|now\s+)*(?:pass(?:es|ed|ing)?|green|clean)\b",
        r"\ball[- ]green\b",
        r"\bpass(?:es|ed|ing)?\s+(?:all|every)\s+(?:the\s+)?(?:\w+\s+)?tests?\b",
        r"\b(?:everything|it all|they all|all of them)\s+pass(?:es|ed)?\b",
        r"\btests?:?\s+\d+\s+pass(?:ed|ing)?\b",
    ],
    "build": [
        r"\bbuilds?\s+(?:now\s+|also\s+)*(?:clean(?:ly)?|successful(?:ly)?|succeed(?:s|ed)|pass(?:es|ed)?|work(?:s|ed)|fine|ok|green|completes?)\b",
        r"\bbuild\s+(?:is|was|now)\s+(?:now\s+)?(?:clean|green|passing|successful|fine|ok)\b",
        r"\b(?:compiles?|compiled)\s+(?:clean(?:ly)?|fine|without|successfully|ok|with no|with zero)\b",
        r"\b(?:built|compiled)\s+successfully\b|\bsuccessfully\s+(?:built|compiled)\b",
        r"\b(?:no|zero|0)\s+(?:new\s+)?(?:compile|compilation|compiler|type|typecheck|lint|linting|build|syntax|tsc|eslint|ruff|clippy|mypy)\s+(?:errors?|warnings?|issues?|problems?)\b",
        r"\b(?:lint(?:ing)?|typecheck(?:ing)?|type[- ]check(?:ing|s)?|tsc|eslint|ruff|clippy|mypy|shellcheck|pyright)\s+(?:(?:is|are|now|all)\s+)*(?:clean|passes|passed|passing|green|happy)\b",
        r"\b(?:lint|type)[- ]clean\b|\bclean build\b",
    ],
    "commit": [
        r"\b(?:i(?:'ve| have)?|we|just|successfully|been|and)\s+committed\b",
        r"\bcommitted\s+(?:as|the|it|them|these|with|everything|all|changes|and|[0-9a-f]{7,})",
        r"\bcreated\s+(?:a\s+|the\s+)?(?:new\s+)?commit\b",
        r"\b(?:changes|work|everything|it|that|this)\s+(?:is|are|has been|have been|now)\s+committed\b",
    ],
    "push": [
        r"\bsuccessfully\s+(?:force[- ])?pushed\b",
        r"\b(?:force[- ])?pushed\s+(?:it |them |this |that |everything |all |the \w+ |\w+ )?(?:up )?to\s+(?:origin|upstream|remote|github|gitlab|main|master|the (?:remote|repo)|\w+/\w+)\b",
        r"\b(?:force[- ])?pushed\s+(?:it|them|everything|all|the (?:commit|commits|changes|branch)|and|[0-9a-f]{7,})\b",
        r"\bpush\s+(?:succeeded|complete[d]?|went through)\b",
    ],
    "pr": [
        r"\b(?:opened|created|raised|filed|submitted)\s+(?:a\s+|the\s+|new\s+)*(?:draft\s+)?(?:pr|pull request|merge request)\b",
        r"\b(?:pr|pull request)\s*#?\d*\s+(?:was\s+|has been\s+)?(?:opened|created)\b",
    ],
    "verify": [
        r"\b(?:i(?:'ve| have)?|we|now|it'?s|is|are|has been|have been|all)\s+(?:now\s+|been\s+)?(?:fixed|resolved)\b",
        r"^(?:fixed|resolved)\b(?![- ]\w+\s+(?:width|height|position|size))",
        r"\b(?:fixed|resolved)\s+(?:the|a|an|that|this|it|both|all|two|three|\d+)\b",
        r"\b(?:works?|working)\s+(?:now|correctly|properly|as expected|fine)\b",
        r"\b(?:is|are|now)\s+(?:now\s+)?working\b",
        r"\b(?:i(?:'ve| have)?|we)\s+(?:verified|confirmed|validated|tested)\b",
        r"\b(?:verified|confirmed)\s+(?:that|it|the|this)\b",
    ],
}
CLAIM_RE = {k: [re.compile(p, I) for p in v] for k, v in CLAIM_PATTERNS.items()}
CHECK_OF = {"test": "tests", "build": "build", "commit": "vcs", "push": "vcs", "pr": "vcs", "verify": "verify"}


def find_claims(text):
    """Claims in assistant text: [{kind, snippet}]. Hedged, negated, quoted and
    code-block text is ignored."""
    claims, seen = [], set()
    for s in sentences(text):
        if "?" in s:
            continue
        low = re.sub(r"\bas expected\b", "as-ex", s, flags=I)
        for kind, pats in CLAIM_RE.items():
            m = next((m for m in (p.search(low) for p in pats) if m), None)
            if not m:
                continue
            if HEDGE.search(low) and not (kind == "build" and not _only_fail_hedge(low)):
                continue
            if kind != "build" and NO_WORDS.search(low) and kind != "verify":
                continue
            if kind == "build" and re.search(r"\b(not|\w+n't|never)\b", low, I):
                continue
            if PAST.search(low):
                continue
            key = (kind, s)
            if key not in seen:
                seen.add(key)
                claims.append({"kind": kind, "snippet": s[:140]})
    # "committed and pushed" style: a push claim without a commit claim is fine.
    # A "verify" claim is dropped when a stronger claim already covers the sentence.
    strong = {c["snippet"] for c in claims if c["kind"] != "verify"}
    return [c for c in claims if not (c["kind"] == "verify" and c["snippet"] in strong)]


def _only_fail_hedge(low):
    """For build claims the HEDGE list includes 'fail/error' words that can
    legitimately sit next to a claim ('no build errors'); only the true hedges
    count there."""
    m = [x.group(0).lower() for x in HEDGE.finditer(low)]
    return bool([w for w in m if not re.match(r"fail|broke|broken", w)])


# ------------------------------------------------------------------ evidence

def _bash_cmds(turn):
    return [t for t in turn["tools"] if t["name"] == "Bash"]


def _matching(turn, pred, extra_res):
    out = []
    for t in _bash_cmds(turn):
        cmd = t["input"].get("command", "") or ""
        hit = any(pred(seg) for seg in command_segments(cmd))
        if not hit:
            for rx in extra_res:
                try:
                    if re.search(rx, cmd):
                        hit = True
                        break
                except re.error:
                    pass
        if hit:
            out.append(t)
    return out


def evaluate(turn, claim, cfg, text=None):
    """Return (status, detail). status: ok | missing | stale | failed | skipped."""
    tools = turn["tools"]
    kind = claim["kind"]
    edits = [t for t in tools if is_code_edit(t)]
    last_edit = max((t["i"] for t in edits), default=-1)
    delegated = any(t["name"] in DELEGATE_TOOLS for t in tools)

    if kind in ("test", "build"):
        pred = is_test_segment if kind == "test" else is_build_segment
        extra = cfg.get("extra_test_commands" if kind == "test" else "extra_build_commands", []) or []
        if kind == "build":
            extra = list(extra) + list(cfg.get("extra_test_commands", []) or [])
        runs = _matching(turn, pred, extra)
        what = "test run" if kind == "test" else "build/lint/typecheck run"
        good = [t for t in runs if not t["err"] and t["i"] > last_edit]
        if good:
            return "ok", "%s at call %d" % (what, good[-1]["i"])
        if delegated:
            return "skipped", "work was delegated to a subagent; cannot verify"
        after = [t for t in runs if t["i"] > last_edit]
        if after:
            if FAILWORDS.search(text or ""):
                return "skipped", "last run errored but the reply discusses failures"
            return "failed", "the last %s this turn exited with an error" % what
        before = [t for t in runs if not t["err"]]
        if before and last_edit >= 0:
            return "stale", "the last %s came before your last edit (%s)" % (what, _edit_name(tools[last_edit]))
        return "missing", "no %s happened this turn" % what

    if kind in ("commit", "push", "pr"):
        runs = _matching(turn, lambda seg: kind in vcs_kinds(seg), [])
        label = {"commit": "git commit", "push": "git push", "pr": "gh pr create"}[kind]
        if any(not t["err"] for t in runs):
            return "ok", "%s ran" % label
        if delegated:
            return "skipped", "work was delegated to a subagent; cannot verify"
        if runs:
            return "failed", "%s errored this turn" % label
        return "missing", "no %s ran this turn" % label

    if kind == "verify":
        if not edits:
            return "skipped", "no code edits this turn"
        executed = delegated or any(
            (t["name"] == "Bash" and bash_is_exec(t["input"].get("command", ""))) or t["name"].startswith("mcp__")
            for t in tools)
        if executed:
            return "ok", "something was executed this turn"
        return "missing", "you edited code but ran nothing this turn"
    return "skipped", ""


def _edit_name(tool):
    inp = tool["input"]
    return os.path.basename(inp.get("file_path") or inp.get("notebook_path") or inp.get("path") or "file")


def check_turn(turn, cfg, text=None):
    """All claims in the turn's final text with their evidence status."""
    text = turn["final_text"] if text is None else text
    res = []
    for c in find_claims(text):
        if not cfg["checks"].get(CHECK_OF[c["kind"]], True):
            continue
        status, detail = evaluate(turn, c, cfg, text)
        res.append(dict(c, status=status, detail=detail))
    return res


def build_reason(findings):
    parts = []
    for f in findings[:3]:
        parts.append('you said "%s" but %s' % (f["snippet"][:90].strip(), f["detail"]))
    return "Argus: " + "; and ".join(parts) + ". Run it now, or say plainly that it is unverified."
