# coding: utf-8

# Phase 4: tests for the JSON API endpoints that do not instantiate
# ocitysmap.OCitySMap (so they need neither the config file nor the GIS
# database). These return JSON directly rather than rendering templates, so no
# context-processor seam is needed -- a plain TestCase suffices.
#
# The config endpoints (paper_formats, layouts, styles, overlays, papersize)
# and the jobs POST path all build an OCitySMap instance and are left for a
# future ocitysmap mock seam.

import json

from django.test import TestCase

from .base import make_job, OcitysmapMockMixin

NONCE = "0123456789abcdef"


class JobStatiApiTest(TestCase):
    def test_returns_non_empty_status_mapping(self):
        response = self.client.get("/apis/job-stati")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content))


class JobsGetApiTest(TestCase):
    def test_bbox_job_details(self):
        job = make_job(status=0, maptitle="ApiJob")
        response = self.client.get("/apis/jobs/%d" % job.id)
        self.assertEqual(response.status_code, 202)          # 202 while waiting
        data = json.loads(response.content)
        self.assertEqual(data["id"], job.id)
        self.assertEqual(data["title"], "ApiJob")
        self.assertIn("bbox_top", data)
        self.assertNotIn("osm_id", data)

    def test_administrative_job_uses_osm_id(self):
        job = make_job(status=0, administrative_osmid=123456,
                       lat_upper_left=None, lon_upper_left=None,
                       lat_bottom_right=None, lon_bottom_right=None)
        data = json.loads(self.client.get("/apis/jobs/%d" % job.id).content)
        self.assertEqual(data["osm_id"], 123456)
        self.assertNotIn("bbox_top", data)

    def test_done_job_returns_200(self):
        job = make_job(status=2, resultmsg="ok")
        self.assertEqual(
            self.client.get("/apis/jobs/%d" % job.id).status_code, 200)

    def test_missing_id_is_404(self):
        self.assertEqual(self.client.get("/apis/jobs").status_code, 404)


class CancelJobApiTest(TestCase):
    def _post(self, payload):
        return self.client.post("/apis/cancel_job", data=json.dumps(payload),
                                content_type="application/json")

    def test_matching_nonce_cancels_the_job(self):
        job = make_job(status=0, nonce=NONCE)
        response = self._post({"id": job.id, "nonce": NONCE})
        self.assertEqual(response.status_code, 204)
        job.refresh_from_db()
        self.assertTrue(job.is_cancelled())

    def test_wrong_nonce_is_forbidden(self):
        job = make_job(status=0, nonce=NONCE)
        response = self._post({"id": job.id, "nonce": "wrongnonce000000"})
        self.assertEqual(response.status_code, 403)
        job.refresh_from_db()
        self.assertFalse(job.is_cancelled())

    def test_missing_fields_is_bad_request(self):
        job = make_job(status=0, nonce=NONCE)
        self.assertEqual(self._post({"id": job.id}).status_code, 400)

    def test_get_is_method_not_allowed(self):
        self.assertEqual(self.client.get("/apis/cancel_job").status_code, 405)

    def test_unknown_id_is_404(self):
        self.assertEqual(self._post({"id": 999999, "nonce": "x"}).status_code, 404)


# --- Config endpoints (these build an OCitySMap instance, hence the mock) ---

class PaperFormatsApiTest(OcitysmapMockMixin, TestCase):
    def test_returns_paper_sizes_with_dimensions(self):
        data = json.loads(self.client.get("/apis/paper_formats").content)
        self.assertEqual(data["Din A4"], {"width": 210, "height": 297})
        self.assertNotIn("Best fit", data)   # entries without dimensions dropped


class LayoutsApiTest(OcitysmapMockMixin, TestCase):
    def test_lists_renderers_with_description_and_preview(self):
        data = json.loads(self.client.get("/apis/layouts").content)
        self.assertIn("plain", data)
        self.assertEqual(data["plain"]["description"],
                         "Full-page map without index")
        self.assertIn("preview_url", data["plain"])


class StylesApiTest(OcitysmapMockMixin, TestCase):
    def test_lists_styles_with_preview(self):
        data = json.loads(self.client.get("/apis/styles").content)
        self.assertIn("MapnikOSM", data)
        self.assertIn("preview_url", data["MapnikOSM"])


class OverlaysApiTest(OcitysmapMockMixin, TestCase):
    def test_lists_overlays(self):
        data = json.loads(self.client.get("/apis/overlays").content)
        self.assertIn("Contour", data)
