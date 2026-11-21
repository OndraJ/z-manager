import datetime

from employees.models import Employee, EmployeeStatus, EmploymentType


def make_employee(**overrides):
    data = {
        "first_name": "Jana",
        "last_name": "Nováková",
        "birth_date": datetime.date(1990, 5, 17),
        "employment_type": EmploymentType.HPP,
        "status": EmployeeStatus.ACTIVE,
    }
    data.update(overrides)
    return Employee.objects.create(**data)
