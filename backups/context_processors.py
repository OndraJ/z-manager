from django.conf import settings


def backup_settings(request):
    return {"backup_email_to": settings.BACKUP_EMAIL_TO}
