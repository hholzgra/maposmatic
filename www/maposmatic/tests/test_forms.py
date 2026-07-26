# coding: utf-8

# Phase 4: validation tests for the simple forms. These forms do no database
# or ocitysmap work in their clean() methods, so they use SimpleTestCase.
#
# MapRenderingJobForm is intentionally NOT covered here: its __init__ builds an
# ocitysmap.OCitySMap instance (reading the config and the GIS database) to
# populate its choice fields, so it needs an ocitysmap mock seam (future work).

from django.test import SimpleTestCase

from www.maposmatic import forms

from .base import OcitysmapMockMixin


class MapSearchFormTest(SimpleTestCase):
    def test_valid_query(self):
        self.assertTrue(forms.MapSearchForm({"query": "paris"}).is_valid())

    def test_query_is_required(self):
        self.assertFalse(forms.MapSearchForm({}).is_valid())

    def test_empty_query_is_invalid(self):
        self.assertFalse(forms.MapSearchForm({"query": ""}).is_valid())


class MapCancelFormTest(SimpleTestCase):
    def test_valid_and_id_coerced_to_int(self):
        form = forms.MapCancelForm({"id": "5", "nonce": "abc"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["id"], 5)

    def test_nonce_is_required(self):
        self.assertFalse(forms.MapCancelForm({"id": "5"}).is_valid())

    def test_id_is_required(self):
        self.assertFalse(forms.MapCancelForm({"nonce": "abc"}).is_valid())

    def test_non_numeric_id_is_invalid(self):
        self.assertFalse(forms.MapCancelForm({"id": "abc", "nonce": "x"}).is_valid())


class MapRecreateFormTest(SimpleTestCase):
    def test_valid_and_id_coerced_to_int(self):
        form = forms.MapRecreateForm({"id": "7"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["id"], 7)

    def test_id_is_required(self):
        self.assertFalse(forms.MapRecreateForm({}).is_valid())


class MapRenderingJobFormTest(OcitysmapMockMixin, SimpleTestCase):
    """The submission form builds an OCitySMap instance in __init__ to populate
    its choice fields, so it needs the ocitysmap mock."""

    def test_choices_are_populated_from_ocitysmap(self):
        form = forms.MapRenderingJobForm()
        layout_names = [choice[0] for choice in form.fields["layout"].choices]
        self.assertIn("plain", layout_names)
        self.assertEqual(form.fields["layout"].initial, "plain")
        self.assertEqual(form.fields["stylesheet"].initial, "MapnikOSM")
