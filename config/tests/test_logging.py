import logging

from django.test import SimpleTestCase


class ErrorLoggingTests(SimpleTestCase):
    def test_django_errors_reach_a_console_handler_without_debug_filter(self):
        # Django's default handler only prints when DEBUG is on (require_debug_true),
        # which would hide server errors on Zuza's laptop.
        handlers = logging.getLogger("django").handlers

        self.assertTrue(any(isinstance(h, logging.StreamHandler) for h in handlers))
        self.assertTrue(all(not h.filters for h in handlers))
        self.assertTrue(logging.getLogger("django.request").isEnabledFor(logging.ERROR))
