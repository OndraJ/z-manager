import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import TestCase, mock

from scripts.check_language import find_problems, main, should_check


class PythonFileTests(TestCase):
    def problems(self, source):
        return find_problems(Path("module.py"), source)

    def test_czech_string_literal_is_allowed(self):
        self.assertEqual(self.problems('message = "Záloha odeslána."\n'), [])

    def test_czech_f_string_is_allowed(self):
        self.assertEqual(self.problems('text = f"Zaměstnanec {name} uložen"\n'), [])

    def test_czech_comment_is_reported(self):
        self.assertEqual(self.problems("x = 1  # uloží zálohu\n"), [(1, "Czech in comment")])

    def test_czech_identifier_is_reported(self):
        self.assertEqual(self.problems("záloha = 1\n"), [(1, "Czech in identifier")])

    def test_czech_docstring_is_reported(self):
        source = 'def f():\n    """Vrátí zálohu."""\n'

        self.assertEqual(self.problems(source), [(2, "Czech in docstring outside „…“ quotes")])

    def test_quoted_example_in_docstring_is_allowed(self):
        source = '"""Sorts „Černá“ before „Zelený“."""\n'

        self.assertEqual(self.problems(source), [])


class TextFileTests(TestCase):
    def test_czech_value_in_script_is_reported(self):
        source = 'const FOLDER_NAME = "Zálohy Zuza\'s Manager";\n'

        self.assertEqual(
            find_problems(Path("script.js"), source), [(1, "Czech outside „…“ quotes")]
        )

    def test_quoted_ui_label_in_docs_is_allowed(self):
        source = "Click the „Zálohovat“ button.\n"

        self.assertEqual(find_problems(Path("README.md"), source), [])

    def test_english_text_passes(self):
        self.assertEqual(find_problems(Path("Makefile"), "test: ## Run tests\n"), [])


class FileSelectionTests(TestCase):
    def test_templates_vendor_and_binary_files_are_skipped(self):
        for path in ("templates/base.html", "static/vendor/x.css", "design/logo.png", "uv.lock"):
            with self.subTest(path=path):
                self.assertFalse(should_check(path))

    def test_code_and_docs_are_checked(self):
        for path in ("AGENTS.md", "employees/views.py", "docs/drive-backup-apps-script.js"):
            with self.subTest(path=path):
                self.assertTrue(should_check(path))


class MainTests(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def run_main(self, files):
        paths = []
        for name, content in files.items():
            path = self.tmp / name
            path.write_text(content, encoding="utf-8")
            paths.append(str(path))
        out = StringIO()
        with redirect_stdout(out):
            code = main(paths)
        return code, out.getvalue()

    def test_returns_1_and_lists_problems(self):
        code, output = self.run_main({"ok.py": "x = 1\n", "bad.js": "const a = 'Zálohy';\n"})

        self.assertEqual(code, 1)
        self.assertIn("bad.js:1: Czech outside „…“ quotes", output)
        self.assertIn("1 problem(s).", output)

    def test_returns_0_when_clean(self):
        code, output = self.run_main({"ok.md": "All English.\n"})

        self.assertEqual((code, output), (0, ""))

    def test_binary_files_are_ignored(self):
        path = self.tmp / "data.bin"
        path.write_bytes(b"\xff\xfe\x00\x81")

        self.assertEqual(main([str(path)]), 0)

    def test_without_arguments_checks_files_tracked_by_git(self):
        clean = self.tmp / "clean.py"
        clean.write_text("x = 1\n")

        with mock.patch("scripts.check_language.tracked_files", return_value=[str(clean)]):
            self.assertEqual(main([]), 0)
