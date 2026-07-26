# coding: utf-8

# Phase 3: CSRF protection regression tests.
#
# These lock in the behaviour established when CsrfViewMiddleware was enabled:
# browser POST views require a token, while the machine-facing API endpoints
# are @csrf_exempt (external clients cannot carry a Django token). We use a
# client with enforce_csrf_checks=True (the normal test client disables CSRF).

from django.middleware.csrf import get_token
from django.test import TestCase, RequestFactory
from django.test.client import Client

from .base import make_job

NONCE = "0123456789abcdef"


def _valid_token_and_cookie():
    """Mint a matching CSRF token + cookie pair, as a rendered page would."""
    request = RequestFactory().get("/")
    token = get_token(request)
    return token, request.META["CSRF_COOKIE"]


class CsrfProtectionTest(TestCase):
    def setUp(self):
        self.csrf_client = Client(enforce_csrf_checks=True)

    def test_browser_post_without_token_is_forbidden(self):
        job = make_job(status=0, nonce=NONCE)
        response = self.csrf_client.post(
            "/cancel/", {"id": job.id, "nonce": NONCE})
        self.assertEqual(response.status_code, 403)
        job.refresh_from_db()
        self.assertFalse(job.is_cancelled())     # request never reached the view

    def test_browser_post_with_valid_token_passes_csrf(self):
        job = make_job(status=0, nonce=NONCE)
        token, cookie = _valid_token_and_cookie()
        self.csrf_client.cookies["csrftoken"] = cookie
        response = self.csrf_client.post(
            "/cancel/", {"id": job.id, "nonce": NONCE}, HTTP_X_CSRFTOKEN=token)
        # gets past CSRF and into the view (which cancels + redirects)
        self.assertNotEqual(response.status_code, 403)
        self.assertEqual(response.status_code, 302)

    def test_api_jobs_is_csrf_exempt(self):
        # No token, yet not blocked by CSRF: 400 comes from the empty payload,
        # not from CSRF (which would be 403).
        response = self.csrf_client.post(
            "/apis/jobs", data="{}", content_type="application/json")
        self.assertNotEqual(response.status_code, 403)

    def test_api_cancel_job_is_csrf_exempt(self):
        response = self.csrf_client.post(
            "/apis/cancel_job", data="{}", content_type="application/json")
        self.assertNotEqual(response.status_code, 403)
