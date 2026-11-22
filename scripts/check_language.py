"""Fail when Czech text appears where only English is allowed (see AGENTS.md).

Czech is allowed only in texts Zuza sees in the app:
- templates (`templates/`) – not checked,
- Python string literals (UI messages, labels, test data) – but not in comments or
  identifiers; docstrings follow the rule for other files,
- other files only inside Czech quotes „…“ (quoting a UI label or an example in docs).

Usage: python scripts/check_language.py [paths...]   (default: all files tracked by git)
"""

import ast
import io
import re
import subprocess
import sys
import tokenize
from pathlib import Path

CZECH = re.compile(r"[áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]")
CZECH_QUOTED = re.compile(r"„[^“]*“")
SKIPPED_PREFIXES = ("templates/", "static/vendor/", "design/")
SKIPPED_SUFFIXES = (".png", ".jpg", ".svg", ".woff", ".woff2", ".lock", ".sqlite3", ".ico")


def find_problems_in_python(source: str) -> list[tuple[int, str]]:
    problems = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type in (tokenize.COMMENT, tokenize.NAME) and CZECH.search(token.string):
            kind = "comment" if token.type == tokenize.COMMENT else "identifier"
            problems.append((token.start[0], f"Czech in {kind}"))

    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            docstring = ast.get_docstring(node, clean=False)
            if docstring and CZECH.search(CZECH_QUOTED.sub("", docstring)):
                problems.append((node.body[0].lineno, "Czech in docstring outside „…“ quotes"))
    return problems


def find_problems_in_text(source: str) -> list[tuple[int, str]]:
    return [
        (number, "Czech outside „…“ quotes")
        for number, line in enumerate(source.splitlines(), start=1)
        if CZECH.search(CZECH_QUOTED.sub("", line))
    ]


def find_problems(path: Path, source: str) -> list[tuple[int, str]]:
    if path.suffix == ".py":
        return find_problems_in_python(source)
    return find_problems_in_text(source)


def should_check(path: str) -> bool:
    return not path.startswith(SKIPPED_PREFIXES) and not path.endswith(SKIPPED_SUFFIXES)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.splitlines()


def main(argv: list[str]) -> int:
    paths = [p for p in (argv or tracked_files()) if should_check(p) and Path(p).is_file()]
    failures = 0
    for name in sorted(paths):
        path = Path(name)
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line, message in find_problems(path, source):
            print(f"{name}:{line}: {message}")
            failures += 1
    if failures:
        print(f"\n{failures} problem(s). Czech is allowed only in texts Zuza sees in the app.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
