# coding: utf-8

# Phase 2 test for the data-backfill logic of migration
# 0038_maprenderingjob_file_prefix.
#
# A full migration *replay* test is not meaningful here: earlier migrations
# contain PostgreSQL-only raw SQL, and the test database is SQLite (see
# www.settings_test). What actually matters -- and what carried real risk for
# the ~500k production rows -- is that the backfill reproduces exactly the
# prefix the model computes at runtime, so existing on-disk files keep
# matching. We test that function directly.

import importlib
from datetime import datetime, timezone

from django.test import SimpleTestCase

from www.maposmatic.models import MapRenderingJob

# The module name starts with a digit, so import it by string.
_mig = importlib.import_module(
    "www.maposmatic.migrations.0038_maprenderingjob_file_prefix")
compute_files_prefix = _mig.compute_files_prefix


class BackfillComputeFilesPrefixTest(SimpleTestCase):
    def test_utc_timestamp_produces_dated_path(self):
        job = MapRenderingJob(
            id=1234, maptitle="Ceci n'est pas Paris",
            startofrendering_time=datetime(2026, 7, 24, 17, 8, tzinfo=timezone.utc),
        )
        self.assertEqual(
            compute_files_prefix(job),
            "2026/07/24/001234_2026-07-24_17-08_ceci-n-est-pas-paris",
        )

    def test_backfill_matches_runtime_files_prefix(self):
        # The critical invariant: the one-off backfill and the live model must
        # compute the same prefix for the same (UTC-stored) row, or historical
        # download links would break.
        job = MapRenderingJob(
            id=987, maptitle="Some Town",
            startofrendering_time=datetime(2025, 12, 31, 23, 59, tzinfo=timezone.utc),
        )
        self.assertEqual(compute_files_prefix(job), job.files_prefix())

    def test_missing_timestamp_falls_back_to_id_and_title(self):
        job = MapRenderingJob(id=42, maptitle="Test Map",
                              startofrendering_time=None)
        self.assertEqual(compute_files_prefix(job), "000042_test-map")
