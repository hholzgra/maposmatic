# coding: utf-8

# Phase 3: behaviour tests for the map list, detail, cancel and recreate
# views. These render templates and/or query the database, so they build on
# RenderedViewTestCase (which neutralises the external side effects of the
# global context processor). The default test client disables CSRF enforcement,
# so the POST endpoints can be exercised without a token here; CSRF enforcement
# itself is covered separately in test_csrf.py.

from www.maposmatic.models import MapRenderingJob

from .base import RenderedViewTestCase, make_job

NONCE = "0123456789abcdef"   # 16 hex chars, matches the URL nonce pattern


class MapListTest(RenderedViewTestCase):
    def test_jobs_appear_in_the_list(self):
        make_job(maptitle="AlphaMap")
        make_job(maptitle="BetaMap")
        response = self.client.get("/maps/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AlphaMap")
        self.assertContains(response, "BetaMap")

    def test_search_with_single_match_redirects_to_the_map(self):
        job = make_job(maptitle="Uniquetitle")
        response = self.client.get("/maps/", {"query": "Uniquetitle"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/maps/%d" % job.id)

    def test_errors_category_lists_only_failed_jobs(self):
        make_job(maptitle="FailedJob", status=2, resultmsg="boom")
        make_job(maptitle="GoodJob", status=2, resultmsg="ok")
        response = self.client.get("/maps/errors")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "FailedJob")
        self.assertNotContains(response, "GoodJob")


class MapDetailTest(RenderedViewTestCase):
    def test_detail_page_renders(self):
        job = make_job(maptitle="Detailtitle")
        response = self.client.get("/maps/%d" % job.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detailtitle")

    def test_unknown_id_is_404(self):
        self.assertEqual(self.client.get("/maps/999999").status_code, 404)

    def test_cancel_form_only_shown_with_matching_nonce(self):
        job = make_job(status=0, nonce=NONCE)
        with_nonce = self.client.get("/maps/%d/%s" % (job.id, NONCE))
        without_nonce = self.client.get("/maps/%d" % job.id)
        self.assertContains(with_nonce, 'action="/cancel/"')
        self.assertNotContains(without_nonce, 'action="/cancel/"')


class CancelViewTest(RenderedViewTestCase):
    def test_cancel_with_matching_nonce_cancels_the_job(self):
        job = make_job(status=0, nonce=NONCE)
        response = self.client.post("/cancel/", {"id": job.id, "nonce": NONCE})
        self.assertEqual(response.status_code, 302)
        job.refresh_from_db()
        self.assertTrue(job.is_cancelled())

    def test_cancel_with_wrong_nonce_is_404(self):
        job = make_job(status=0, nonce=NONCE)
        response = self.client.post(
            "/cancel/", {"id": job.id, "nonce": "ffffffffffffffff"})
        self.assertEqual(response.status_code, 404)
        job.refresh_from_db()
        self.assertFalse(job.is_cancelled())

    def test_cancel_get_is_bad_request(self):
        self.assertEqual(self.client.get("/cancel/").status_code, 400)


class RecreateViewTest(RenderedViewTestCase):
    def test_recreate_clones_the_job_and_redirects(self):
        job = make_job(maptitle="Clonable", status=2)
        before = MapRenderingJob.objects.count()
        response = self.client.post("/recreate/", {"id": job.id})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MapRenderingJob.objects.count(), before + 1)
        newest = MapRenderingJob.objects.latest("id")
        self.assertEqual(newest.maptitle, "Clonable")
        self.assertTrue(newest.is_waiting())      # status reset to submitted
        self.assertNotEqual(newest.id, job.id)

    def test_recreate_get_is_bad_request(self):
        self.assertEqual(self.client.get("/recreate/").status_code, 400)
