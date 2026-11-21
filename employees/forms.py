from django import forms

from employees.models import Employee, EmploymentType


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["first_name", "last_name", "birth_date", "employment_type", "status"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "birth_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
            "employment_type": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Django's "- Select an option -" blank label has no Czech translation yet.
        self.fields["employment_type"].choices = [("", "– vyberte –"), *EmploymentType.choices]
        for name, field in self.fields.items():
            if self.errors.get(name):
                field.widget.attrs["class"] += " is-invalid"


class EmployeeStatusForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["status"]
