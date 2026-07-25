# coding: utf-8

# Phase 0 smoke test.
#
# Its only jobs are to prove that the test harness is wired up and that
# `./manage.py test --settings=www.settings_test` runs green. It deliberately
# exercises a pure, dependency-free function (no database, no network), so it
# uses SimpleTestCase (which forbids database access).

from django.test import SimpleTestCase

from www.maposmatic.context_processors import content_security_policy


class HarnessSmokeTest(SimpleTestCase):
    def test_content_security_policy_has_expected_directives(self):
        csp = content_security_policy()
        self.assertIn("default-src 'self'", csp)
        self.assertIn("img-src 'self' data:", csp)
        self.assertIn("script-src 'self' 'unsafe-inline'", csp)
        self.assertIn("style-src 'self' 'unsafe-inline'", csp)
