from django.db import models
from django.db.models.functions import Collate

from employees.collation import COLLATION_NAME
from employees.validators import validate_not_in_future


class EmploymentType(models.TextChoices):
    HPP = "hpp", "HPP"
    BRIGADA = "brigada", "Brigáda"


class EmployeeStatus(models.TextChoices):
    ACTIVE = "active", "Aktivní"
    SICK = "sick", "Nemocný"
    TERMINATED = "terminated", "Ukončený"


# Display order of statuses: active first, terminated last.
STATUS_ORDER = [EmployeeStatus.ACTIVE, EmployeeStatus.SICK, EmployeeStatus.TERMINATED]


class EmployeeQuerySet(models.QuerySet):
    def ordered(self):
        """Canonical ordering: by status (active, sick, terminated), then by name."""
        status_rank = models.Case(
            *(models.When(status=status, then=rank) for rank, status in enumerate(STATUS_ORDER)),
            default=len(STATUS_ORDER),
            output_field=models.IntegerField(),
        )
        return self.annotate(status_rank=status_rank).order_by(
            "status_rank",
            Collate("last_name", COLLATION_NAME),
            Collate("first_name", COLLATION_NAME),
        )


class Employee(models.Model):
    first_name = models.CharField("Jméno", max_length=100)
    last_name = models.CharField("Příjmení", max_length=100)
    birth_date = models.DateField("Datum narození", validators=[validate_not_in_future])
    employment_type = models.CharField(
        "Pracovní poměr", max_length=20, choices=EmploymentType.choices
    )
    status = models.CharField(
        "Status", max_length=20, choices=EmployeeStatus.choices, default=EmployeeStatus.ACTIVE
    )

    objects = EmployeeQuerySet.as_manager()

    class Meta:
        verbose_name = "Zaměstnanec"
        verbose_name_plural = "Zaměstnanci"

    def __str__(self):
        return f"{self.last_name} {self.first_name}"
