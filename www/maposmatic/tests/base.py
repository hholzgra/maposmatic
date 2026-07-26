# coding: utf-8

# Shared base class for tests that render full HTML pages.
#
# This module is intentionally NOT named test*.py so the test runner does not
# try to collect tests from it.

from unittest import mock

from django.test import TestCase

from www.maposmatic.models import MapRenderingJob


def make_job(**kwargs):
    """Create and persist a MapRenderingJob with sensible required-field
    defaults (including a bounding box, which the detail page needs to
    render); override any field via kwargs."""
    defaults = dict(
        maptitle="Test Map", stylesheet="MapnikOSM", layout="plain",
        paper_width_mm=210, paper_height_mm=297,
        status=0, index_queue_at_submission=0, queue="default",
        lat_upper_left=48.8, lon_upper_left=2.0,
        lat_bottom_right=48.7, lon_bottom_right=2.1,
    )
    defaults.update(kwargs)
    return MapRenderingJob.objects.create(**defaults)


class RenderedViewTestCase(TestCase):
    """Base class for tests that render full pages through the templates.

    The global ``www.maposmatic.context_processors.all`` context processor
    runs on *every* request and reaches out to external systems: it shells out
    to ``systemctl`` to check whether the render daemons are running, and it
    queries the separate PostGIS databases for their last-update timestamps.
    None of that exists in the test environment, so this base class patches
    those boundaries to deterministic values, keeping page-rendering tests
    fast, isolated and warning-free.

    Subclasses may set ``daemons_running = False`` to simulate stopped render
    daemons.
    """

    #: what is_daemon_running() reports for every queue during the test
    daemons_running = True

    def setUp(self):
        super().setUp()
        boundaries = [
            ("www.settings.is_daemon_running",
                {"return_value": self.daemons_running}),
            ("www.maposmatic.context_processors.get_osm_database_last_update",
                {"return_value": None}),
            ("www.maposmatic.context_processors.get_waymarked_database_last_update",
                {"return_value": None}),
            ("www.maposmatic.context_processors.get_osmnames_table_ok",
                {"return_value": True}),
        ]
        for target, kwargs in boundaries:
            patcher = mock.patch(target, **kwargs)
            patcher.start()
            self.addCleanup(patcher.stop)
