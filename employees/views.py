from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from config.utils import get_safe_next_url
from employees.forms import EmployeeForm, EmployeeStatusForm
from employees.models import Employee, EmployeeStatus, EmploymentType

SAVED_MESSAGE = "Zaměstnanec %(last_name)s %(first_name)s byl uložen."


class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    context_object_name = "employees"

    def get_filters(self):
        """Return valid filter values from the query string; invalid values are ignored."""
        filters = {}
        status = self.request.GET.get("status")
        if status in EmployeeStatus.values:
            filters["status"] = status
        employment_type = self.request.GET.get("employment_type")
        if employment_type in EmploymentType.values:
            filters["employment_type"] = employment_type
        return filters

    def get_queryset(self):
        return Employee.objects.filter(**self.get_filters()).ordered()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = self.get_filters()
        context["status_filter"] = filters.get("status", "")
        context["employment_type_filter"] = filters.get("employment_type", "")
        context["status_choices"] = [
            ("", "Vše"),
            (EmployeeStatus.ACTIVE, "Aktivní"),
            (EmployeeStatus.SICK, "Nemocní"),
            (EmployeeStatus.TERMINATED, "Ukončení"),
        ]
        context["employment_type_choices"] = [("", "Vše"), *EmploymentType.choices]
        context["all_status_choices"] = EmployeeStatus.choices
        return context


class EmployeeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    success_url = reverse_lazy("employees:list")
    success_message = SAVED_MESSAGE


class EmployeeUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    success_url = reverse_lazy("employees:list")
    success_message = SAVED_MESSAGE


class EmployeeStatusUpdateView(LoginRequiredMixin, UpdateView):
    """Inline status change from the list; returns to the list with the same filters."""

    model = Employee
    form_class = EmployeeStatusForm
    http_method_names = ["post"]

    def get_success_url(self):
        return get_safe_next_url(self.request, default=reverse("employees:list"))

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Status zaměstnance {self.object} změněn na „{self.object.get_status_display()}“.",
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Status se nepodařilo změnit.")
        return super().form_invalid(form)
