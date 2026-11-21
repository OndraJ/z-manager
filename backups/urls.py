from django.urls import path

from backups.views import BackupView

urlpatterns = [
    path("backup/", BackupView.as_view(), name="backup"),
]
