import smtplib
import sqlite3
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import transaction
from django.test import TransactionTestCase, override_settings
from django.urls import reverse

from backups.services import BackupNotConfiguredError, send_backup_email
from employees.tests.factories import make_employee

BACKUP_URL = reverse("backup")


# TransactionTestCase: the SQLite backup cannot run inside the transaction TestCase opens.


@override_settings(BACKUP_EMAIL_TO=["zuza@example.com"])
class SendBackupEmailTests(TransactionTestCase):
    def test_sends_database_copy_as_attachment(self):
        make_employee(last_name="Zálohová")

        recipients = send_backup_email()

        self.assertEqual(recipients, ["zuza@example.com"])
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["zuza@example.com"])
        self.assertIn("Záloha Zuza’s Manager", message.subject)
        filename, content, mimetype = message.attachments[0]
        self.assertRegex(filename, r"^zuzas-manager-\d{4}-\d{2}-\d{2}-\d{4}\.sqlite3$")
        self.assertEqual(mimetype, "application/vnd.sqlite3")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / filename
            path.write_bytes(content)
            db = sqlite3.connect(path)
            names = [row[0] for row in db.execute("SELECT last_name FROM employees_employee")]
            db.close()
        self.assertEqual(names, ["Zálohová"])

    @override_settings(BACKUP_EMAIL_TO=[])
    def test_missing_recipient_raises(self):
        with self.assertRaises(BackupNotConfiguredError):
            send_backup_email()
        self.assertEqual(mail.outbox, [])

    def test_refuses_to_run_inside_transaction_instead_of_hanging(self):
        with transaction.atomic(), self.assertRaises(RuntimeError):
            send_backup_email()


@override_settings(BACKUP_EMAIL_TO=["zuza@example.com", "ondra@example.com"])
class BackupViewTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="zuza", password="x")
        self.client.force_login(self.user)

    def test_login_required(self):
        self.client.logout()

        response = self.client.post(BACKUP_URL)

        self.assertRedirects(response, f"{reverse('login')}?next={BACKUP_URL}")
        self.assertEqual(mail.outbox, [])

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(BACKUP_URL).status_code, 405)

    def test_success_returns_to_previous_page_with_message(self):
        next_url = reverse("employees:list")

        response = self.client.post(BACKUP_URL, {"next": next_url}, follow=True)

        self.assertRedirects(response, next_url)
        self.assertContains(response, "Záloha odeslána na zuza@example.com, ondra@example.com.")
        self.assertEqual(len(mail.outbox), 1)

    def test_external_next_url_is_ignored(self):
        response = self.client.post(BACKUP_URL, {"next": "https://evil.example/"})

        self.assertRedirects(response, reverse("dashboard"))

    @override_settings(BACKUP_EMAIL_TO=[])
    def test_not_configured_shows_error(self):
        response = self.client.post(BACKUP_URL, follow=True)

        self.assertContains(response, "Zálohování není nastavené")

    def test_smtp_failure_shows_error(self):
        for error in (smtplib.SMTPAuthenticationError(535, b"bad"), OSError("offline")):
            with self.subTest(error=type(error).__name__):
                with (
                    mock.patch("backups.views.send_backup_email", side_effect=error),
                    self.assertLogs("backups.views", level="ERROR"),
                ):
                    response = self.client.post(BACKUP_URL, follow=True)

                self.assertContains(response, "Zálohu se nepodařilo odeslat.")

    def test_sidebar_button_opens_confirmation_modal_with_recipients(self):
        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, 'data-bs-target="#backup-modal"')
        self.assertContains(response, 'id="backup-modal"')
        self.assertContains(response, f'action="{BACKUP_URL}"')
        self.assertContains(response, "Opravdu chcete poslat zálohu databáze na e-mail")
        self.assertContains(response, "zuza@example.com, ondra@example.com")
        self.assertContains(response, "Odeslat zálohu")

    @override_settings(BACKUP_EMAIL_TO=[])
    def test_modal_without_recipient_explains_and_hides_send_button(self):
        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Zálohování není nastavené")
        self.assertNotContains(response, "Odeslat zálohu")
