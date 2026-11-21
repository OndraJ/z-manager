from django.test import SimpleTestCase, TestCase

from employees.collation import czech_sort_key
from employees.models import Employee
from employees.tests.factories import make_employee


class CzechSortKeyTests(SimpleTestCase):
    def assertSorted(self, expected):
        self.assertEqual(sorted(reversed(expected), key=czech_sort_key), expected)

    def test_hacek_letters_follow_their_base_letter(self):
        self.assertSorted(["Cibulka", "Čapek", "Dvořák"])
        self.assertSorted(["Rychlá", "Řezníček", "Svoboda", "Šimek", "Zeman", "Žák"])

    def test_ch_comes_after_h(self):
        self.assertSorted(["Horák", "Chalupa", "Ivanov"])

    def test_other_accents_only_break_ties(self):
        self.assertSorted(["Ábel", "Adam", "Adámek"])
        self.assertSorted(["Kral", "Král", "Kralová"])

    def test_case_insensitive(self):
        self.assertSorted(["adam", "Bára", "cyril"])


class CzechCollationInDatabaseTests(TestCase):
    def test_queryset_ordered_uses_czech_collation(self):
        for name in ["Zelený", "Černá", "Chalupa", "Horák", "Cibulka"]:
            make_employee(last_name=name)

        names = [e.last_name for e in Employee.objects.ordered()]

        self.assertEqual(names, ["Cibulka", "Černá", "Horák", "Chalupa", "Zelený"])
