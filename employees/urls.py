from django.urls import path

from employees import views

app_name = "employees"

urlpatterns = [
    path("", views.EmployeeListView.as_view(), name="list"),
    path("new/", views.EmployeeCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.EmployeeUpdateView.as_view(), name="update"),
    path("<int:pk>/status/", views.EmployeeStatusUpdateView.as_view(), name="update_status"),
]
