import sqlite3
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.core.management import CommandError, call_command
from django.test import TransactionTestCase

from backups.services import write_database_copy
from employees.models import Employee
from employees.tests.factories import make_employee


class RestoreBackupCommandTests(TransactionTestCase):
    """TransactionTestCase: restoring replaces the whole database, outside a transaction."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def restore(self, path, **options):
        out = StringIO()
        call_command(
            "restore_backup", str(path), noinput=True, safety_dir=self.tmp / "safety",
            stdout=out, **options,
        )  # fmt: skip
        return out.getvalue()

    def test_restores_data_from_backup_and_keeps_safety_copy(self):
        make_employee(last_name="Původní")
        backup = self.tmp / "backup.sqlite3"
        write_database_copy(backup)
        Employee.objects.all().delete()
        make_employee(last_name="Novější")

        output = self.restore(backup)

        self.assertEqual([e.last_name for e in Employee.objects.all()], ["Původní"])
        self.assertIn("Database restored", output)
        safety_copies = list((self.tmp / "safety").glob("before-restore-*.sqlite3"))
        self.assertEqual(len(safety_copies), 1)
        db = sqlite3.connect(safety_copies[0])
        names = [row[0] for row in db.execute("SELECT last_name FROM employees_employee")]
        db.close()
        self.assertEqual(names, ["Novější"])

    def test_rejects_missing_file(self):
        with self.assertRaisesMessage(CommandError, "File not found"):
            self.restore(self.tmp / "nope.sqlite3")

    def test_rejects_file_that_is_not_sqlite(self):
        photo = self.tmp / "photo.jpg"
        photo.write_bytes(b"\xff\xd8\xff\xe0 definitely not a database" * 100)

        with self.assertRaisesMessage(CommandError, "Not a valid SQLite database"):
            self.restore(photo)

    def test_rejects_foreign_sqlite_database(self):
        foreign = self.tmp / "other.sqlite3"
        db = sqlite3.connect(foreign)
        db.execute("CREATE TABLE notes (text TEXT)")
        db.close()

        with self.assertRaisesMessage(CommandError, "Not a Zuza's Manager backup"):
            self.restore(foreign)

    def test_rejected_file_leaves_data_untouched(self):
        make_employee(last_name="Zůstávám")
        bad = self.tmp / "bad.sqlite3"
        bad.write_text("garbage")

        with self.assertRaises(CommandError):
            self.restore(bad)

        self.assertEqual([e.last_name for e in Employee.objects.all()], ["Zůstávám"])
        self.assertFalse((self.tmp / "safety").exists())

    def test_restore_is_cancelled_without_confirmation(self):
        make_employee(last_name="Zůstávám")
        backup = self.tmp / "backup.sqlite3"
        write_database_copy(backup)
        Employee.objects.all().delete()

        for answer in ("no", EOFError):
            with (
                self.subTest(answer=answer),
                mock.patch("builtins.input", side_effect=[answer]),
                self.assertRaisesMessage(CommandError, "Restore cancelled."),
            ):
                call_command("restore_backup", str(backup), stdout=StringIO())

        self.assertFalse(Employee.objects.exists())
