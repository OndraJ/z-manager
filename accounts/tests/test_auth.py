from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

PASSWORD = "spravne-heslo-123"


class AuthFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="zuza", password=PASSWORD)

    def test_login_page_renders_form(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')

    def test_valid_login_redirects_to_dashboard(self):
        response = self.client.post(reverse("login"), {"username": "zuza", "password": PASSWORD})

        self.assertRedirects(response, reverse("dashboard"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_redirects_to_next_url(self):
        response = self.client.post(
            reverse("login"),
            {"username": "zuza", "password": PASSWORD, "next": reverse("dashboard")},
        )

        self.assertRedirects(response, reverse("dashboard"))

    def test_wrong_password_stays_on_login_with_error(self):
        response = self.client.post(
            reverse("login"), {"username": "zuza", "password": "spatne-heslo"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertContains(response, "alert-danger")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logged_in_user_visiting_login_is_redirected_to_dashboard(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("login"))

        self.assertRedirects(response, reverse("dashboard"))

    def test_logout_requires_login_again(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")


class AccountSetupTests(TestCase):
    def test_admin_is_not_available(self):
        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 404)

    def test_every_request_extends_the_session_by_24_hours(self):
        self.client.force_login(get_user_model().objects.create_user(username="zuza"))

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.cookies["sessionid"]["max-age"], 24 * 60 * 60)
