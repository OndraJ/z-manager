import json
import shutil
import tempfile
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest import TestCase, mock

from scripts.claude_hooks import (
    PROJECT_DIR,
    STAGE_SEPARATELY,
    check_bash_command,
    format_python,
    guard_bash,
    main,
    run_quality_gate,
    split_commands,
    working_tree_problem,
)


class SplitCommandsTests(TestCase):
    def test_splits_on_operators_and_respects_quotes(self):
        self.assertEqual(
            split_commands('cd x && git commit -m "a; b" | cat'),
            [["cd", "x"], ["git", "commit", "-m", "a; b"], ["cat"]],
        )

    def test_splits_on_newlines(self):
        self.assertEqual(
            split_commands("make check\ngit status"), [["make", "check"], ["git", "status"]]
        )


class CheckBashCommandTests(TestCase):
    def assertAllowed(self, command):
        self.assertIsNone(check_bash_command(command)[0], command)

    def assertBlocked(self, command, reason_part):
        reason, _ = check_bash_command(command)
        self.assertIsNotNone(reason, command)
        self.assertIn(reason_part, reason)

    def test_allows_normal_commands(self):
        for command in (
            "make check",
            "git status",
            "git diff --stat",
            'git commit -m "Add employee filters"',
            "git checkout -- employees/views.py",
            "git branch",
            "git branch -a --show-current",
            "git log --grep=Co-Authored-By",
            "docker compose down",
            "docker compose -p zm-test down -v",
            "ZM_PORT=8001 docker compose -p zm-test -f compose.yaml down --volumes",
            "COMPOSE_PROJECT_NAME=zm-test docker compose down -v",
        ):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_mentioning_forbidden_commands_in_text_is_allowed(self):
        for command in (
            'grep -n "git push" README.md',
            "echo 'git switch main'",
            'git commit -m "Explain why git push and git switch are blocked"',
            'rg "docker compose down -v" AGENTS.md',
        ):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_blocks_push(self):
        self.assertBlocked("git push -u origin main", "Pushing")
        self.assertBlocked("git -C /repo push", "Pushing")
        self.assertBlocked("make check && git push", "Pushing")

    def test_blocks_branch_changes(self):
        for command in (
            "git switch main",
            "git checkout -b feature",
            "git branch feature/x",
            "git branch -D old",
        ):
            with self.subTest(command=command):
                self.assertBlocked(command, "branches")

    def test_blocks_history_rewrites(self):
        for command in (
            "git commit --amend --no-edit",
            "git rebase -i HEAD~3",
            "git reset --hard HEAD~1",
        ):
            with self.subTest(command=command):
                self.assertBlocked(command, "Rewriting history")

    def test_blocks_ai_attribution_trailer_in_commit(self):
        command = 'git commit -m "Add x\n\nCo-Authored-By: Claude <noreply@anthropic.com>"'

        self.assertBlocked(command, "Co-Authored-By")

    def test_requires_staging_in_a_separate_command(self):
        self.assertBlocked('git add -A && git commit -m "Add x"', STAGE_SEPARATELY)

    def test_blocks_removing_developer_volumes(self):
        self.assertBlocked("docker compose down -v", "zm-test")
        self.assertBlocked("docker compose -p z_manager down --volumes", "zm-test")
        self.assertBlocked("docker-compose down -v", "zm-test")
        self.assertBlocked("docker volume rm z_manager_data", "volumes")

    def test_heredoc_with_apostrophe_falls_back_to_line_checks(self):
        message = "git commit -F - <<'MSG'\nAdd Zuza's backup\nMSG"
        self.assertEqual(check_bash_command(message), (None, True))
        self.assertBlocked("echo 'it's\ngit push", "Pushing")

    def test_reports_whether_command_commits(self):
        self.assertEqual(check_bash_command('git commit -m "x"'), (None, True))
        self.assertEqual(check_bash_command("git status"), (None, False))


class WorkingTreeProblemTests(TestCase):
    def problem(self, porcelain, commit_all=False):
        result = mock.Mock(stdout=porcelain)
        with mock.patch("subprocess.run", return_value=result):
            return working_tree_problem(commit_all)

    def test_fully_staged_tree_is_fine(self):
        self.assertIsNone(self.problem("M  a.py\nA  b.py\nD  c.py\n"))

    def test_unstaged_and_untracked_changes_are_reported(self):
        problem = self.problem("M  a.py\n M b.py\n?? c.py\n")

        self.assertIn(" M b.py", problem)
        self.assertIn("?? c.py", problem)
        self.assertNotIn("a.py", problem)

    def test_commit_all_accepts_unstaged_tracked_changes(self):
        self.assertIsNone(self.problem(" M b.py\n D c.py\n", commit_all=True))
        self.assertIsNotNone(self.problem("?? new.py\n", commit_all=True))


class GuardBashTests(TestCase):
    def run_guard(self, command):
        stderr = StringIO()
        with redirect_stderr(stderr):
            code = guard_bash({"tool_input": {"command": command}})
        return code, stderr.getvalue()

    def test_blocked_command_exits_with_2_and_reason(self):
        code, stderr = self.run_guard("git push")

        self.assertEqual(code, 2)
        self.assertIn("Blocked by project hook: Pushing", stderr)

    @mock.patch("scripts.claude_hooks.working_tree_problem", return_value=None)
    @mock.patch("scripts.claude_hooks.run_quality_gate", return_value=None)
    def test_commit_runs_quality_gate(self, gate, tree):
        code, _ = self.run_guard('git commit -m "Add x"')

        self.assertEqual(code, 0)
        tree.assert_called_once_with(False)
        gate.assert_called_once()

    @mock.patch("scripts.claude_hooks.working_tree_problem", return_value=None)
    @mock.patch("scripts.claude_hooks.run_quality_gate", return_value=None)
    def test_commit_all_flag_is_passed_on(self, gate, tree):
        self.run_guard('git commit -am "Add x"')

        tree.assert_called_once_with(True)

    @mock.patch("scripts.claude_hooks.working_tree_problem", return_value="unstaged b.py")
    @mock.patch("scripts.claude_hooks.run_quality_gate")
    def test_commit_with_leftover_changes_is_blocked_before_running_gate(self, gate, tree):
        code, stderr = self.run_guard('git commit -m "Add x"')

        self.assertEqual(code, 2)
        self.assertIn("unstaged b.py", stderr)
        gate.assert_not_called()

    @mock.patch("scripts.claude_hooks.working_tree_problem", return_value=None)
    @mock.patch("scripts.claude_hooks.run_quality_gate", return_value="make check failed")
    def test_commit_is_blocked_when_quality_gate_fails(self, gate, tree):
        code, stderr = self.run_guard('git commit -m "Add x"')

        self.assertEqual(code, 2)
        self.assertIn("make check failed", stderr)

    @mock.patch("scripts.claude_hooks.run_quality_gate")
    def test_other_commands_skip_quality_gate(self, gate):
        code, _ = self.run_guard("git status")

        self.assertEqual(code, 0)
        gate.assert_not_called()


class RunQualityGateTests(TestCase):
    def test_returns_none_when_make_check_passes(self):
        with mock.patch("subprocess.run", return_value=mock.Mock(returncode=0)):
            self.assertIsNone(run_quality_gate())

    def test_returns_output_tail_when_make_check_fails(self):
        failed = mock.Mock(returncode=2, stdout="line\n" * 50 + "FAILED (failures=1)", stderr="")
        with mock.patch("subprocess.run", return_value=failed):
            reason = run_quality_gate()

        self.assertIn("FAILED (failures=1)", reason)
        self.assertLessEqual(reason.count("line"), 30)


class FormatPythonTests(TestCase):
    def project_tmp_file(self, content):
        directory = Path(tempfile.mkdtemp(dir=PROJECT_DIR))
        self.addCleanup(shutil.rmtree, directory)
        path = directory / "module.py"
        path.write_text(content)
        return path

    def test_ignores_non_python_files(self):
        with mock.patch("subprocess.run") as run:
            self.assertEqual(format_python({"tool_input": {"file_path": "README.md"}}), 0)
        run.assert_not_called()

    def test_ignores_files_outside_the_project(self):
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, directory)
        path = directory / "elsewhere.py"
        path.write_text("x=1\n")
        with mock.patch("subprocess.run") as run:
            self.assertEqual(format_python({"tool_input": {"file_path": str(path)}}), 0)
        run.assert_not_called()

    def test_formats_but_never_removes_unused_imports(self):
        path = self.project_tmp_file("x=1\n")
        ok = mock.Mock(returncode=0, stdout="")
        with mock.patch("subprocess.run", return_value=ok) as run:
            code = format_python({"tool_input": {"file_path": str(path)}})

        self.assertEqual(code, 0)
        self.assertEqual(run.call_count, 2)
        check_args = run.call_args_list[1].args[0]
        self.assertIn("--unfixable", check_args)
        self.assertIn("F401,F841", check_args)

    def test_unused_import_survives_for_real(self):
        path = self.project_tmp_file("import os\n")

        with redirect_stderr(StringIO()) as stderr:
            code = format_python({"tool_input": {"file_path": str(path)}})

        self.assertEqual(path.read_text(), "import os\n")
        self.assertEqual(code, 2)
        self.assertIn("F401", stderr.getvalue())

    def test_reports_unfixable_problems(self):
        path = self.project_tmp_file("x = undefined\n")
        results = [mock.Mock(returncode=0), mock.Mock(returncode=1, stdout="F821 undefined")]
        stderr = StringIO()
        with mock.patch("subprocess.run", side_effect=results), redirect_stderr(stderr):
            code = format_python({"tool_input": {"file_path": str(path)}})

        self.assertEqual(code, 2)
        self.assertIn("F821", stderr.getvalue())


class MainTests(TestCase):
    def test_dispatches_to_hook(self):
        stdin = StringIO(json.dumps({"tool_input": {"command": "git status"}}))

        self.assertEqual(main(["guard-bash"], stdin=stdin), 0)

    def test_unknown_hook_prints_usage(self):
        stderr = StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(main(["nope"], stdin=StringIO("{}")), 1)
        self.assertIn("Usage", stderr.getvalue())
