import logging
import smtplib

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View

from backups.services import BackupNotConfiguredError, send_backup_email
from config.utils import get_safe_next_url

logger = logging.getLogger(__name__)


class BackupView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request):
        try:
            recipients = send_backup_email()
        except BackupNotConfiguredError:
            messages.error(
                request, "Zálohování není nastavené – chybí e-mailová adresa pro zálohy."
            )
        except smtplib.SMTPException, OSError:
            logger.exception("Sending the backup e-mail failed")
            messages.error(
                request,
                "Zálohu se nepodařilo odeslat. Zkontrolujte připojení k internetu "
                "a zkuste to znovu.",
            )
        else:
            messages.success(request, f"Záloha odeslána na {', '.join(recipients)}.")
        return redirect(get_safe_next_url(request, default=reverse("dashboard")))
