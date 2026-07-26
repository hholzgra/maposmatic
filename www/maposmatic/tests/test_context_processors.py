# coding: utf-8

# Phase 1 unit tests for the Content-Security-Policy builder.
#
# content_security_policy() reads www.settings.MAP_TILE_SOURCES and
# EXTERNAL_IMAGE_SOURCES as *module attributes*, so Django's @override_settings
# (which patches django.conf.settings) does NOT affect it -- these tests patch
# the module attributes directly instead.

from unittest import mock

from django.test import SimpleTestCase

from www.maposmatic.context_processors import content_security_policy


class ContentSecurityPolicyTest(SimpleTestCase):
    def test_default_policy_has_all_directives(self):
        csp = content_security_policy()
        self.assertIn("default-src 'self'", csp)
        self.assertIn("img-src 'self' data:", csp)
        self.assertIn("script-src 'self' 'unsafe-inline'", csp)
        self.assertIn("style-src 'self' 'unsafe-inline'", csp)

    @mock.patch("www.settings.EXTERNAL_IMAGE_SOURCES", ["https://img.example.org/"])
    @mock.patch("www.settings.MAP_TILE_SOURCES", ["https://tiles.example.org/"])
    def test_configured_sources_are_merged_into_img_src(self):
        # Tile sources come first, then the other external image sources, both
        # after the always-present 'self' and data: entries.
        csp = content_security_policy()
        self.assertIn(
            "img-src 'self' data: "
            "https://tiles.example.org/ https://img.example.org/",
            csp,
        )

    @mock.patch("www.settings.EXTERNAL_IMAGE_SOURCES", [])
    @mock.patch("www.settings.MAP_TILE_SOURCES", [])
    def test_img_src_without_external_sources_is_self_and_data_only(self):
        csp = content_security_policy()
        self.assertIn("img-src 'self' data:; script-src", csp)
