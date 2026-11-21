from django.urls import include, path

urlpatterns = [
    path("", include("accounts.urls")),
    path("", include("dashboard.urls")),
    path("employees/", include("employees.urls")),
    path("", include("backups.urls")),
]
