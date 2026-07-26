# coding: utf-8

# Phase 2 tests for MapRenderingJob behaviour that touches the database:
# the status state-machine transitions and the manager query methods.
#
# These use TestCase (each test runs in a rolled-back transaction against the
# throwaway SQLite test database configured in www.settings_test).

import os
import re
from datetime import datetime, timezone

from django.test import TestCase

import www.settings
from www.maposmatic.models import MapRenderingJob


def make_job(**kwargs):
    """Create and persist a MapRenderingJob with sensible required-field
    defaults; override any field via kwargs."""
    defaults = dict(
        maptitle="Test Map", stylesheet="MapnikOSM", layout="plain",
        paper_width_mm=210, paper_height_mm=297,
        status=0, index_queue_at_submission=0, queue="default",
    )
    defaults.update(kwargs)
    return MapRenderingJob.objects.create(**defaults)


class StateMachineTest(TestCase):
    def test_start_rendering(self):
        job = make_job()
        job.start_rendering()

        self.assertEqual(job.status, 1)
        # timestamp is set and timezone-aware (UTC)
        self.assertIsNotNone(job.startofrendering_time)
        self.assertIsNotNone(job.startofrendering_time.tzinfo)
        # file_prefix is computed once and persisted
        self.assertTrue(job.file_prefix)
        self.assertEqual(job.file_prefix, job.files_prefix())
        self.assertRegex(
            job.file_prefix,
            r"^\d{4}/\d{2}/\d{2}/\d{6}_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}_test-map$",
        )

        # persisted, not just set in memory
        reloaded = MapRenderingJob.objects.get(pk=job.pk)
        self.assertEqual(reloaded.status, 1)
        self.assertEqual(reloaded.file_prefix, job.file_prefix)

    def test_end_rendering(self):
        job = make_job(status=1)
        job.end_rendering("ok")

        self.assertEqual(job.status, 2)
        self.assertEqual(job.resultmsg, "ok")
        self.assertIsNotNone(job.endofrendering_time)
        self.assertIsNotNone(job.endofrendering_time.tzinfo)
        self.assertTrue(MapRenderingJob.objects.get(pk=job.pk).is_done())

    def test_cancel(self):
        job = make_job(status=0)
        job.cancel()

        self.assertEqual(job.status, 4)
        self.assertEqual(job.resultmsg, "rendering cancelled")
        self.assertIsNotNone(job.endofrendering_time)
        # timezone-aware (UTC), like start/end_rendering -- guards against the
        # naive-datetime regression this test originally surfaced
        self.assertIsNotNone(job.endofrendering_time.tzinfo)
        self.assertTrue(MapRenderingJob.objects.get(pk=job.pk).is_cancelled())


class ManagerTest(TestCase):
    def test_to_render_filters_by_status_and_queue(self):
        waiting = make_job(status=0, queue="default")
        make_job(status=1, queue="default")          # rendering, excluded
        make_job(status=2, queue="default")          # done, excluded
        make_job(status=0, queue="api")              # other queue, excluded

        result = list(MapRenderingJob.objects.to_render("default"))
        self.assertEqual(result, [waiting])

    def test_to_render_orders_by_submission_time(self):
        a = make_job()
        b = make_job()
        c = make_job()
        # submission_time is auto_now_add, so override it explicitly (update()
        # bypasses auto_now_add) to get a deterministic order: c, a, b.
        MapRenderingJob.objects.filter(pk=c.pk).update(
            submission_time=datetime(2026, 1, 1, tzinfo=timezone.utc))
        MapRenderingJob.objects.filter(pk=a.pk).update(
            submission_time=datetime(2026, 1, 2, tzinfo=timezone.utc))
        MapRenderingJob.objects.filter(pk=b.pk).update(
            submission_time=datetime(2026, 1, 3, tzinfo=timezone.utc))

        result = list(MapRenderingJob.objects.to_render("default"))
        self.assertEqual([j.pk for j in result], [c.pk, a.pk, b.pk])

    def test_queue_size_counts_only_waiting_jobs_in_queue(self):
        make_job(status=0, queue="default")
        make_job(status=0, queue="default")
        make_job(status=1, queue="default")   # rendering
        make_job(status=0, queue="api")        # other queue

        self.assertEqual(MapRenderingJob.objects.queue_size("default"), 2)
        self.assertEqual(MapRenderingJob.objects.queue_size("api"), 1)

    def test_get_by_filename_matches_a_rendered_job(self):
        job = make_job()
        job.start_rendering()   # persists file_prefix

        name = os.path.join(
            www.settings.RENDERING_RESULT_PATH, job.files_prefix()) + ".pdf"
        self.assertEqual(MapRenderingJob.objects.get_by_filename(name), job)

    def test_get_by_filename_returns_none_for_wrong_prefix(self):
        job = make_job()
        job.start_rendering()

        # right id in the basename, but a path that is not the job's prefix
        name = os.path.join(
            www.settings.RENDERING_RESULT_PATH,
            "2000/01/01/%06d_2000-01-01_00-00_wrong.pdf" % job.id)
        self.assertIsNone(MapRenderingJob.objects.get_by_filename(name))

    def test_get_by_filename_returns_none_for_unknown_id(self):
        name = os.path.join(
            www.settings.RENDERING_RESULT_PATH,
            "999999_2026-01-01_00-00_ghost.pdf")
        self.assertIsNone(MapRenderingJob.objects.get_by_filename(name))
