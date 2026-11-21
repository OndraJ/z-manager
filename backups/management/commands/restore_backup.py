import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone

from backups.services import ensure_no_open_transaction, write_database_copy

# Tables that identify a Zuza's Manager database.
REQUIRED_TABLES = {"django_migrations", "auth_user", "employees_employee"}


class Command(BaseCommand):
    help = (
        "Replace the current database with a backup file. A safety copy of the current "
        "database is written first, then migrations are applied."
    )

    def add_arguments(self, parser):
        parser.add_argument("backup_file", type=Path)
        parser.add_argument(
            "--safety-dir",
            type=Path,
            help="Where to write the safety copy (default: next to the database file).",
        )
        parser.add_argument("--noinput", action="store_true", help="Do not ask for confirmation.")

    def handle(self, backup_file: Path, safety_dir: Path | None, noinput: bool, **options):
        self.validate(backup_file)

        if not noinput:
            try:
                answer = input(
                    "This replaces ALL current data with the backup. Type 'yes' to continue: "
                )
            except EOFError:
                answer = ""
            if answer.strip().lower() != "yes":
                raise CommandError("Restore cancelled.")

        safety_dir = safety_dir or Path(settings.DATABASES["default"]["NAME"]).parent
        safety_dir.mkdir(parents=True, exist_ok=True)
        safety_copy = safety_dir / f"before-restore-{timezone.now():%Y%m%d-%H%M%S}.sqlite3"
        write_database_copy(safety_copy)
        self.stdout.write(f"Safety copy of the current data: {safety_copy}")

        ensure_no_open_transaction()
        source = sqlite3.connect(f"file:{backup_file}?mode=ro", uri=True)
        try:
            connection.ensure_connection()
            source.backup(connection.connection)
        finally:
            source.close()

        call_command("migrate", interactive=False, verbosity=0)
        self.stdout.write(self.style.SUCCESS(f"Database restored from {backup_file}."))

    def validate(self, backup_file: Path) -> None:
        if not backup_file.is_file():
            raise CommandError(f"File not found: {backup_file}")
        try:
            source = sqlite3.connect(f"file:{backup_file}?mode=ro", uri=True)
            try:
                tables = {
                    row[0]
                    for row in source.execute("SELECT name FROM sqlite_master WHERE type='table'")
                }
                integrity = source.execute("PRAGMA integrity_check").fetchone()[0]
            finally:
                source.close()
        except sqlite3.DatabaseError as exc:
            raise CommandError(f"Not a valid SQLite database ({exc}): {backup_file}") from exc

        missing = REQUIRED_TABLES - tables
        if missing:
            raise CommandError(
                f"Not a Zuza's Manager backup (missing tables: {', '.join(sorted(missing))})."
            )
        if integrity != "ok":
            raise CommandError(f"The backup file is damaged: {integrity}")
