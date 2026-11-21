from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DashboardViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="zuza", password="x")

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_logged_in_user_sees_dashboard_with_sidebar(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/index.html")
        self.assertContains(response, 'class="zm-sidebar"')
        self.assertContains(response, 'aria-current="page"')
        self.assertContains(response, "Pracovní plocha")

    def test_header_shows_hotel_links_and_logout(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard"))

        for link in settings.HOTEL_LINKS:
            with self.subTest(link=link["label"]):
                self.assertContains(response, f'href="{link["url"]}"')
        self.assertContains(response, 'target="_blank"', count=len(settings.HOTEL_LINKS))
        self.assertContains(response, f'action="{reverse("logout")}"')
