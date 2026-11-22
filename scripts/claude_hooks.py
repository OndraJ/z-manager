"""Claude Code hooks for this project (configured in .claude/settings.json).

guard-bash     PreToolUse on Bash – blocks commands that AGENTS.md forbids and runs
               the quality gate before `git commit`.
format-python  PostToolUse on Edit/Write – formats an edited .py file and reports lint
               problems ruff cannot fix safely.

Hooks read the tool call as JSON on stdin. Exit code 2 blocks the call (PreToolUse) or
reports a problem back to the agent (PostToolUse); the reason is printed to stderr.
"""

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
TEST_PROJECT = "zm-test"
SEPARATORS = {";", "&&", "||", "|", "&", "(", ")", "\n"}
ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# git options that take a separate value, e.g. `git -C path status`
GIT_OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
AI_TRAILER = re.compile(r"co-authored-by", re.IGNORECASE)
# Rules for `git commit` that keep the quality gate meaningful (see working_tree_problem).
STAGE_SEPARATELY = (
    "Stage files with `git add` in a separate command, then run `git commit` alone – "
    "the hook checks the commit content before the command runs."
)


def split_commands(command: str) -> list[list[str]]:
    """Split a shell command line into simple commands (lists of words), honouring quotes."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    commands, current = [], []
    for token in lexer:
        if token in SEPARATORS or set(token) <= set(";&|()\n"):
            if current:
                commands.append(current)
            current = []
        else:
            current.append(token)
    if current:
        commands.append(current)
    return commands


def strip_env(words: list[str]) -> tuple[dict[str, str], list[str]]:
    env = {}
    while words and ENV_ASSIGNMENT.match(words[0]):
        name, _, value = words[0].partition("=")
        env[name] = value
        words = words[1:]
    return env, words


def git_subcommand(args: list[str]) -> tuple[str, list[str]]:
    """Return (subcommand, its arguments) for the words after `git`."""
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in GIT_OPTIONS_WITH_VALUE else 1
    if i >= len(args):
        return "", []
    return args[i], args[i + 1 :]


def check_git(sub: str, args: list[str]) -> str | None:
    if sub == "push":
        return "Pushing is done by the developer, not by the agent."
    if sub == "switch" or (sub == "checkout" and {"-b", "-B"} & set(args)):
        return "Creating or switching branches is done by the developer."
    if sub == "branch" and any(not a.startswith("-") for a in args):
        return "Creating, renaming or deleting branches is done by the developer."
    if (
        sub in {"rebase", "filter-branch"}
        or (sub == "commit" and "--amend" in args)
        or (sub == "reset" and "--hard" in args)
    ):
        return "Rewriting history is done by the developer."
    return None


def check_docker(words: list[str], env: dict[str, str]) -> str | None:
    if words[:2] == ["docker", "volume"] and len(words) > 2 and words[2] in {"rm", "prune"}:
        return (
            "Removing Docker volumes can delete the developer's data – leave it to the developer."
        )
    is_compose = words[:2] == ["docker", "compose"] or words[:1] == ["docker-compose"]
    if not is_compose or "down" not in words or not {"-v", "--volumes"} & set(words):
        return None
    project = env.get("COMPOSE_PROJECT_NAME")
    for i, word in enumerate(words):
        if word in {"-p", "--project-name"} and i + 1 < len(words):
            project = words[i + 1]
        elif word.startswith("--project-name="):
            project = word.partition("=")[2]
    if project != TEST_PROJECT:
        return (
            f"`docker compose down -v` is allowed only for the `{TEST_PROJECT}` project "
            "(use `make verify-down`) – the default project holds the developer's data."
        )
    return None


def check_bash_command(command: str) -> tuple[str | None, bool]:
    """Return (reason to block or None, whether the command runs `git commit`)."""
    try:
        commands = split_commands(command)
    except ValueError:
        # Not valid shell for shlex (e.g. a heredoc body containing an apostrophe):
        # fall back to checking each line split on whitespace, without quote handling.
        commands = [line.split() for line in re.split(r"\n|&&|\|\||;|\|", command)]

    is_commit = adds_files = False
    for words in commands:
        env, words = strip_env(words)
        if not words:
            continue
        if words[0] == "git":
            sub, args = git_subcommand(words[1:])
            reason = check_git(sub, args)
            if reason:
                return reason, False
            is_commit = is_commit or sub == "commit"
            adds_files = adds_files or sub in {"add", "rm", "mv"}
        else:
            reason = check_docker(words, env)
            if reason:
                return reason, False

    if is_commit and AI_TRAILER.search(command):
        return (
            "Commit messages must not contain a Co-Authored-By trailer or any AI attribution.",
            True,
        )
    if is_commit and adds_files:
        return STAGE_SEPARATELY, True
    return None, is_commit


def working_tree_problem(commit_all: bool) -> str | None:
    """`make check` runs on the working tree, so it must equal what is being committed."""
    status = subprocess.run(
        ["git", "status", "--porcelain"],  # noqa: S607
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    leftovers = [
        line
        for line in status
        if line.startswith("??") or (line[1] != " " and not (commit_all and line[1] in "MD"))
    ]
    if not leftovers:
        return None
    listing = "\n".join(leftovers[:10])
    return (
        "The working tree has changes that are not part of this commit, so `make check` "
        f"would not test what is committed. Stage them or move them away first:\n{listing}"
    )


def run_quality_gate() -> str | None:
    """Run `make check`; return an error summary if it fails."""
    result = subprocess.run(
        ["make", "check"],  # noqa: S607
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return None
    tail = "\n".join((result.stdout + result.stderr).strip().splitlines()[-30:])
    return f"`make check` failed – fix it before committing:\n{tail}"


def guard_bash(payload: dict) -> int:
    command = payload.get("tool_input", {}).get("command", "")
    reason, is_commit = check_bash_command(command)
    if reason is None and is_commit:
        commit_all = bool(re.search(r"\s(-a|-am|--all)\b", command))
        reason = working_tree_problem(commit_all) or run_quality_gate()
    if reason:
        print(f"Blocked by project hook: {reason}", file=sys.stderr)
        return 2
    return 0


def format_python(payload: dict) -> int:
    file_path = payload.get("tool_input", {}).get("file_path", "")
    path = Path(file_path).resolve()
    if path.suffix != ".py" or not path.is_file() or not path.is_relative_to(PROJECT_DIR):
        return 0
    # The path was checked above to be a .py file inside the project; no shell is used.
    ruff = ["uv", "run", "--quiet", "ruff"]
    subprocess.run(  # noqa: S603
        [*ruff, "format", str(path)], cwd=PROJECT_DIR, capture_output=True, check=False
    )
    # Unused imports/variables are reported but never removed automatically: an agent
    # often adds an import in one edit and the code using it in the next one.
    result = subprocess.run(  # noqa: S603
        [
            *ruff,
            "check",
            "--fix",
            "--unfixable",
            "F401,F841",
            "--output-format",
            "concise",
            str(path),
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(
            "ruff found problems (fix them, or ignore unused imports you are about to use):\n"
            f"{result.stdout.strip()}",
            file=sys.stderr,
        )
        return 2
    return 0


HOOKS = {"guard-bash": guard_bash, "format-python": format_python}


def main(argv: list[str], stdin=sys.stdin) -> int:
    if len(argv) != 1 or argv[0] not in HOOKS:
        print(f"Usage: claude_hooks.py {{{'|'.join(HOOKS)}}}", file=sys.stderr)
        return 1
    return HOOKS[argv[0]](json.load(stdin))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
