# coding: utf-8

# Phase 3: smoke tests that prove the render seam works.
#
# Each simple GET page is rendered all the way through base.html, the global
# context processor and every custom template tag. A 200 here means the whole
# template + context-processor stack renders without raising -- which catches
# template syntax errors, missing context variables and broken template tags.

from .base import RenderedViewTestCase


class PageRenderTest(RenderedViewTestCase):
    SIMPLE_PAGES = [
        "/",
        "/about/",
        "/about/api/",
        "/about/user-guide/",
        "/privacy/",
        "/donate/",
        "/maps/",
    ]

    def test_simple_pages_render(self):
        for url in self.SIMPLE_PAGES:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_rendered_page_carries_the_csp_meta(self):
        # End-to-end proof that the CONTENT_SECURITY_POLICY context value
        # actually reaches the template as the <meta http-equiv> tag.
        response = self.client.get("/privacy/")
        self.assertContains(response, 'http-equiv="Content-Security-Policy"')
