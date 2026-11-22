import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from employees.models import Employee, EmployeeStatus, EmploymentType
from employees.tests.factories import make_employee

LIST_URL = reverse("employees:list")
CREATE_URL = reverse("employees:create")


def valid_form_data(**overrides):
    data = {
        "first_name": "Karel",
        "last_name": "Dvořák",
        "birth_date": "1992-03-04",
        "employment_type": EmploymentType.BRIGADA,
        "status": EmployeeStatus.ACTIVE,
    }
    data.update(overrides)
    return data


class LoginRequiredTests(TestCase):
    def test_all_employee_urls_require_login(self):
        employee = make_employee()
        urls = [
            ("get", LIST_URL),
            ("get", CREATE_URL),
            ("get", reverse("employees:update", args=[employee.pk])),
            ("post", reverse("employees:update_status", args=[employee.pk])),
        ]
        for method, url in urls:
            with self.subTest(url=url):
                response = getattr(self.client, method)(url)
                self.assertRedirects(response, f"{reverse('login')}?next={url}")


class EmployeeViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="zuza", password="x")

    def setUp(self):
        self.client.force_login(self.user)


class EmployeeListTests(EmployeeViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.active_hpp = make_employee(last_name="Aktivní-HPP")
        cls.active_brigada = make_employee(
            last_name="Aktivní-Brigáda", employment_type=EmploymentType.BRIGADA
        )
        cls.sick_hpp = make_employee(last_name="Nemocný-HPP", status=EmployeeStatus.SICK)
        cls.terminated_brigada = make_employee(
            last_name="Ukončený-Brigáda",
            employment_type=EmploymentType.BRIGADA,
            status=EmployeeStatus.TERMINATED,
        )

    def listed(self, query=""):
        response = self.client.get(LIST_URL + query)
        self.assertEqual(response.status_code, 200)
        return [e.last_name for e in response.context["employees"]]

    def test_lists_all_employees_in_status_order(self):
        self.assertEqual(
            self.listed(),
            ["Aktivní-Brigáda", "Aktivní-HPP", "Nemocný-HPP", "Ukončený-Brigáda"],
        )

    def test_filter_by_status(self):
        self.assertEqual(self.listed("?status=sick"), ["Nemocný-HPP"])

    def test_filter_by_employment_type(self):
        self.assertEqual(
            self.listed("?employment_type=brigada"), ["Aktivní-Brigáda", "Ukončený-Brigáda"]
        )

    def test_filters_combine(self):
        self.assertEqual(self.listed("?status=active&employment_type=hpp"), ["Aktivní-HPP"])

    def test_invalid_filter_values_are_ignored(self):
        self.assertEqual(len(self.listed("?status=nonsense&employment_type=xyz")), 4)

    def test_empty_filter_result_shows_message(self):
        self.active_hpp.delete()

        response = self.client.get(LIST_URL + "?status=active&employment_type=hpp")

        self.assertContains(response, "Žádný zaměstnanec neodpovídá vybranému filtru.")

    def test_sidebar_item_is_active(self):
        response = self.client.get(LIST_URL)

        self.assertContains(response, "Správa zaměstnanců")
        self.assertRegex(response.content.decode(), rf'href="{LIST_URL}"\s+class="nav-link active"')


class EmployeeCreateUpdateTests(EmployeeViewTestCase):
    def test_create_page_renders_form(self):
        response = self.client.get(CREATE_URL)

        self.assertContains(response, "Nový zaměstnanec")
        self.assertContains(response, 'type="date"')
        self.assertContains(response, "– vyberte –")
        self.assertNotContains(response, "Select an option")

    def test_create_valid_employee(self):
        response = self.client.post(CREATE_URL, valid_form_data(), follow=True)

        self.assertRedirects(response, LIST_URL)
        employee = Employee.objects.get()
        self.assertEqual(employee.last_name, "Dvořák")
        self.assertEqual(employee.birth_date, datetime.date(1992, 3, 4))
        self.assertContains(response, "Zaměstnanec Dvořák Karel byl uložen.")

    def test_create_with_missing_fields_shows_errors(self):
        response = self.client.post(CREATE_URL, {})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context["form"].errors),
            {"first_name", "last_name", "birth_date", "employment_type", "status"},
        )
        self.assertFalse(Employee.objects.exists())

    def test_create_with_future_birth_date_fails(self):
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)

        response = self.client.post(CREATE_URL, valid_form_data(birth_date=tomorrow.isoformat()))

        self.assertContains(response, "Datum nesmí být v budoucnosti.")
        self.assertContains(response, "is-invalid")
        self.assertFalse(Employee.objects.exists())

    def test_edit_page_is_prefilled(self):
        employee = make_employee()

        response = self.client.get(reverse("employees:update", args=[employee.pk]))

        self.assertContains(response, "Upravit zaměstnance")
        self.assertContains(response, 'value="1990-05-17"')

    def test_update_employee(self):
        employee = make_employee()
        url = reverse("employees:update", args=[employee.pk])

        response = self.client.post(
            url, valid_form_data(first_name="Jana", last_name="Malá", status="sick")
        )

        self.assertRedirects(response, LIST_URL)
        employee.refresh_from_db()
        self.assertEqual(employee.last_name, "Malá")
        self.assertEqual(employee.status, EmployeeStatus.SICK)


class EmployeeStatusUpdateTests(EmployeeViewTestCase):
    def setUp(self):
        super().setUp()
        self.employee = make_employee()
        self.url = reverse("employees:update_status", args=[self.employee.pk])

    def test_changes_status_and_returns_to_filtered_list(self):
        next_url = f"{LIST_URL}?status=active&employment_type="

        response = self.client.post(self.url, {"status": "sick", "next": next_url}, follow=True)

        self.assertRedirects(response, next_url)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.status, EmployeeStatus.SICK)
        self.assertContains(response, "změněn na „Nemocný“")

    def test_only_status_is_changed(self):
        self.client.post(self.url, {"status": "terminated", "last_name": "Hacker"})

        self.employee.refresh_from_db()
        self.assertEqual(self.employee.status, EmployeeStatus.TERMINATED)
        self.assertEqual(self.employee.last_name, "Nováková")

    def test_external_next_url_is_ignored(self):
        response = self.client.post(self.url, {"status": "sick", "next": "https://evil.example/"})

        self.assertRedirects(response, LIST_URL)

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_invalid_status_is_rejected_and_returns_to_filtered_list(self):
        next_url = f"{LIST_URL}?status=active&employment_type="

        response = self.client.post(self.url, {"status": "fired", "next": next_url}, follow=True)

        self.assertRedirects(response, next_url)
        self.assertContains(response, "Status se nepodařilo změnit.")
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.status, EmployeeStatus.ACTIVE)
