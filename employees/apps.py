from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    name = "employees"

    def ready(self):
        from employees.collation import connect_signal

        connect_signal()
