"""Database backup: copy the SQLite database and e-mail it."""

import sqlite3
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import connection
from django.utils import dateformat, timezone


class BackupNotConfiguredError(Exception):
    """No recipient is configured in BACKUP_EMAIL_TO."""


def ensure_no_open_transaction() -> None:
    # sqlite3's backup() retries forever while the connection has an open write
    # transaction, so fail fast instead of hanging the request.
    if connection.in_atomic_block:
        raise RuntimeError("The SQLite backup cannot run inside a database transaction.")


def write_database_copy(target: Path) -> None:
    """Write a consistent copy of the live database to `target` (SQLite online backup)."""
    ensure_no_open_transaction()
    connection.ensure_connection()
    destination = sqlite3.connect(target)
    try:
        connection.connection.backup(destination)
    finally:
        destination.close()


def send_backup_email() -> list[str]:
    """E-mail a copy of the database to BACKUP_EMAIL_TO. Returns the recipients."""
    recipients = settings.BACKUP_EMAIL_TO
    if not recipients:
        raise BackupNotConfiguredError

    now = timezone.localtime()
    with tempfile.TemporaryDirectory() as tmp:
        backup_path = Path(tmp) / "backup.sqlite3"
        write_database_copy(backup_path)
        content = backup_path.read_bytes()

    readable_time = dateformat.format(now, "j. n. Y H:i")
    message = EmailMessage(
        subject=f"Záloha Zuza’s Manager – {readable_time}",
        body=(
            "Dobrý den,\n\n"
            f"v příloze je záloha dat aplikace Zuza’s Manager z {readable_time}.\n\n"
            "E-mail si nechte v poště – ze zálohy půjde v případě potřeby obnovit všechna data.\n"
        ),
        to=recipients,
    )
    message.attach(f"zuzas-manager-{now:%Y-%m-%d-%H%M}.sqlite3", content, "application/vnd.sqlite3")
    message.send()
    return recipients
