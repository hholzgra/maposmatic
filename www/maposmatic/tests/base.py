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
        overlay="",
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


class _FakeConfigItem:
    """Attribute bag standing in for an ocitysmap renderer / style / overlay
    configuration object."""

    def __init__(self, name, description="", url="", group="", annotation=""):
        self.name = name
        self.description = description
        self.url = url
        self.group = group
        self.annotation = annotation


class FakeOCitySMap:
    """Minimal stand-in for ocitysmap.OCitySMap. Returns small, valid data
    shapes without reading the config file or touching the GIS database, so
    the views/forms/APIs that construct an OCitySMap instance can be tested.

    Only the read-only "catalogue" methods are implemented -- the geographic
    lookups (get_geographic_info, get_paper_size_by_name) used by the
    bbox/polygon/papersize/jobs-POST endpoints are intentionally left out;
    those need real GIS data and are out of scope here.
    """

    RENDERERS = [
        _FakeConfigItem("plain", "Full-page map without index"),
        _FakeConfigItem("single_page_index_side", "Map with index on the side"),
    ]
    STYLES = [_FakeConfigItem("MapnikOSM", "OpenStreetMap default")]
    OVERLAYS = [_FakeConfigItem("Contour", "Contour lines")]
    PAPER_SIZES = [("Din A4", 210, 297), ("Best fit", None, None)]

    def __init__(self, *args, **kwargs):
        pass

    def get_all_renderers(self):
        return list(self.RENDERERS)

    def get_all_renderer_names(self):
        return [r.name for r in self.RENDERERS]

    def get_all_indexers(self):
        return ["StreetIndex", "PoiIndex"]

    def get_all_indexers_name_desc(self):
        return [("StreetIndex", "Street index"), ("PoiIndex", "POI index")]

    def get_all_style_configurations(self):
        return list(self.STYLES)

    def get_all_style_names(self):
        return [s.name for s in self.STYLES]

    def get_all_overlay_configurations(self):
        return list(self.OVERLAYS)

    def get_all_overlay_names(self):
        return [o.name for o in self.OVERLAYS]

    def get_all_paper_sizes(self, section=None):
        return list(self.PAPER_SIZES)

    def translate(self, text):
        return text


class OcitysmapMockMixin:
    """Test-case mixin that replaces ocitysmap.OCitySMap with FakeOCitySMap for
    the duration of each test. Compose it before the concrete TestCase base,
    e.g. ``class T(OcitysmapMockMixin, TestCase)``."""

    def setUp(self):
        super().setUp()
        patcher = mock.patch("ocitysmap.OCitySMap", FakeOCitySMap)
        patcher.start()
        self.addCleanup(patcher.stop)
