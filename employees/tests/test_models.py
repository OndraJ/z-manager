import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from employees.models import Employee, EmployeeStatus, EmploymentType
from employees.tests.factories import make_employee


class EmployeeModelTests(TestCase):
    def test_default_status_is_active(self):
        employee = Employee.objects.create(
            first_name="Petr",
            last_name="Svoboda",
            birth_date=datetime.date(1985, 1, 1),
            employment_type=EmploymentType.BRIGADA,
        )

        self.assertEqual(employee.status, EmployeeStatus.ACTIVE)

    def test_str_is_last_name_first(self):
        self.assertEqual(str(make_employee()), "Nováková Jana")

    def test_ordered_by_status_then_name(self):
        make_employee(last_name="Adam", status=EmployeeStatus.TERMINATED)
        make_employee(last_name="Zelený", status=EmployeeStatus.ACTIVE)
        make_employee(last_name="Beneš", status=EmployeeStatus.SICK)
        make_employee(last_name="Černá", status=EmployeeStatus.ACTIVE)

        names = [e.last_name for e in Employee.objects.ordered()]

        self.assertEqual(names, ["Černá", "Zelený", "Beneš", "Adam"])

    def test_future_birth_date_is_invalid(self):
        employee = Employee(
            first_name="Jan",
            last_name="Budoucí",
            birth_date=timezone.localdate() + datetime.timedelta(days=1),
            employment_type=EmploymentType.HPP,
        )

        with self.assertRaises(ValidationError) as ctx:
            employee.full_clean()

        self.assertIn("birth_date", ctx.exception.message_dict)

    def test_today_birth_date_is_valid(self):
        employee = Employee(
            first_name="Jan",
            last_name="Dnešní",
            birth_date=timezone.localdate(),
            employment_type=EmploymentType.HPP,
        )

        employee.full_clean()
