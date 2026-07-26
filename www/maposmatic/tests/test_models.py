# coding: utf-8

# Phase 1 unit tests for MapRenderingJob helper methods.
#
# These all run on *unsaved* model instances and touch neither the database
# nor any external service, so they use SimpleTestCase (which forbids DB access
# and would fail loudly if any of these methods started issuing queries).

from datetime import datetime, timezone
from unittest import mock

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

from django.test import SimpleTestCase

from www.maposmatic.models import MapRenderingJob


class FilesPrefixTest(SimpleTestCase):
    def test_utc_timestamp_builds_dated_path(self):
        job = MapRenderingJob(
            id=1234, maptitle="Ceci n'est pas Paris",
            startofrendering_time=datetime(2026, 7, 24, 17, 8, tzinfo=timezone.utc),
        )
        self.assertEqual(
            job.files_prefix(),
            "2026/07/24/001234_2026-07-24_17-08_ceci-n-est-pas-paris",
        )

    def test_aware_non_utc_timestamp_is_converted_to_utc(self):
        # Regression guard: a Europe/Berlin-aware timestamp (19:08 +02:00) must
        # be rendered in UTC (17:08), not with the local wall-clock digits.
        # This is exactly the bug that motivated the file_prefix / UTC fix.
        if ZoneInfo is None:  # pragma: no cover
            self.skipTest("zoneinfo not available")
        job = MapRenderingJob(
            id=1234, maptitle="x",
            startofrendering_time=datetime(2026, 7, 24, 19, 8,
                                           tzinfo=ZoneInfo("Europe/Berlin")),
        )
        self.assertEqual(job.files_prefix(),
                         "2026/07/24/001234_2026-07-24_17-08_x")

    def test_stored_file_prefix_is_used_verbatim(self):
        # Once persisted, the stored prefix wins and no recomputation happens.
        job = MapRenderingJob(id=1, maptitle="ignored title")
        job.file_prefix = "2020/01/01/000001_2020-01-01_00-00_frozen"
        self.assertEqual(job.files_prefix(), job.file_prefix)

    def test_missing_timestamp_falls_back_to_id_and_title(self):
        job = MapRenderingJob(id=42, maptitle="Test Map",
                              startofrendering_time=None)
        self.assertEqual(job.files_prefix(), "000042_test-map")

    def test_result_is_cached(self):
        job = MapRenderingJob(
            id=7, maptitle="Cached",
            startofrendering_time=datetime(2026, 1, 2, 3, 4, tzinfo=timezone.utc),
        )
        first = job.files_prefix()
        self.assertIs(job.files_prefix(), first)


class MaptitleComputizedTest(SimpleTestCase):
    def test_modern_titles_are_slugified(self):
        cases = {
            "Ceci n'est pas Paris": "ceci-n-est-pas-paris",
            "  Multiple   Spaces  ": "multiple-spaces",
            "Bonn/Bad Godesberg": "bonn-bad-godesberg",
            "Münster": "munster",
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(
                    MapRenderingJob(id=5, maptitle=title).maptitle_computized(),
                    expected,
                )

    def test_legacy_ids_use_ascii_stripping(self):
        # For ids <= LAST_OLD_ID the old (pre-slugify) scheme is kept, so the
        # computed name still matches historic on-disk files.
        with mock.patch("www.settings.LAST_OLD_ID", 1000):
            self.assertEqual(
                MapRenderingJob(id=5, maptitle="Ceci n'est pas Paris")
                .maptitle_computized(),
                "CecinestpasParis",
            )
            self.assertEqual(
                MapRenderingJob(id=5, maptitle="Bonn/Bad Godesberg")
                .maptitle_computized(),
                "BonnBadGodesberg",
            )


class StatusHelperTest(SimpleTestCase):
    # status -> (waiting, rendering, needs_waiting, done, obsolete, cancelled)
    MATRIX = [
        (0, True,  False, True,  False, False, False),
        (1, False, True,  True,  False, False, False),
        (2, False, False, False, True,  False, False),
        (3, False, False, False, False, True,  False),
        (4, False, False, False, False, False, True),
    ]

    def test_status_helpers(self):
        for (s, waiting, rendering, needs, done, obsolete, cancelled) in self.MATRIX:
            job = MapRenderingJob(id=1, status=s)
            with self.subTest(status=s):
                self.assertEqual(job.is_waiting(), waiting)
                self.assertEqual(job.is_rendering(), rendering)
                self.assertEqual(job.needs_waiting(), needs)
                self.assertEqual(job.is_done(), done)
                self.assertEqual(job.is_obsolete(), obsolete)
                self.assertEqual(job.is_cancelled(), cancelled)

    def test_is_done_ok_requires_done_status_and_ok_result(self):
        self.assertTrue(
            MapRenderingJob(id=1, status=2, resultmsg="ok").is_done_ok())
        self.assertFalse(
            MapRenderingJob(id=1, status=2, resultmsg="boom").is_done_ok())
        self.assertFalse(
            MapRenderingJob(id=1, status=1, resultmsg="ok").is_done_ok())
