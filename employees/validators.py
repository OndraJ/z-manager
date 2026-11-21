from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_not_in_future(value):
    if value > timezone.localdate():
        raise ValidationError("Datum nesmí být v budoucnosti.", code="future_date")
