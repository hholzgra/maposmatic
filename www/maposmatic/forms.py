# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2009  David Decotigny
# Copyright (C) 2009  Frédéric Lehobey
# Copyright (C) 2009  Pierre Mauduit
# Copyright (C) 2009  David Mentré
# Copyright (C) 2009  Maxime Petazzoni
# Copyright (C) 2009  Thomas Petazzoni
# Copyright (C) 2009  Gaël Utard
# Copyright (C) 2019  Hartmut Holzgraefe

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Forms for MapOSMatic

from django import forms
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _
from django.forms.utils import ErrorList
import time

import ocitysmap
from www.maposmatic import models, widgets
import www.settings

from multiupload.fields import MultiFileField

class MapSearchForm(forms.Form):
    """
    The map search form, allowing search through the rendered maps.
    """

    query = forms.CharField(min_length=1, required=True,
                widget=forms.TextInput(attrs=
                    {'placeholder': _('Search for a map'),
                     'class': 'span2'}))

class MapRenderingJobForm(forms.ModelForm):
    """
    The main map rendering form, displayed on the 'Create Map' page. It's a
    ModelForm based on the MapRenderingJob model.
    """
    class Meta:
        model = models.MapRenderingJob
        fields = ('layout', 'indexer', 'stylesheet', 'overlay',
                  'maptitle', 'administrative_city',
                  'lat_upper_left', 'lon_upper_left',
                  'lat_bottom_right', 'lon_bottom_right',
                  'submittermail')

    mode = forms.CharField(initial='bbox', widget=forms.HiddenInput)
    layout = forms.ChoiceField(choices=(), widget=forms.Select(attrs= { 'onchange' : 'clearPaperSize(this.value); $("#layout-preview").attr("src","/media/img/layout/"+this.value+".png");'}))
    indexer = forms.ChoiceField(choices=(), widget=forms.Select())
    stylesheet = forms.ChoiceField(choices=(), widget=forms.Select(attrs= { 'onchange' : '$("#style-preview").attr("src","/media/img/style/"+this.value+".jpg");'}))
    overlay = forms.MultipleChoiceField(choices=(), widget=forms.SelectMultiple(attrs= { 'class': 'multipleSelect' }), required=False)
    paper_width_mm = forms.IntegerField(widget=forms.NumberInput(attrs= {'onchange' : 'change_papersize();', 'style': 'width: 5em;'}), min_value=100, max_value=2000)
    paper_height_mm = forms.IntegerField(widget=forms.NumberInput(attrs= {'onchange' : 'change_papersize();', 'style': 'width: 5em;'}), min_value=100, max_value=2000)
    maptitle = forms.CharField(max_length=256, required=False)
    bbox = widgets.AreaField(label=_("Area"),
                             fields=(forms.FloatField(), forms.FloatField(),
                                     forms.FloatField(), forms.FloatField()))
    uploadfile = MultiFileField(required=False)

    map_lang_flag_list = []
    for lang_key, lang_name in www.settings.MAP_LANGUAGES_LIST:
        if lang_key == 'C':
            map_lang_flag_list.append((lang_key, lang_name))
        else:
            country_code = lang_key[3:5].lower()
            lang_html = mark_safe("<span class='flag-icon flag-icon-%s'> </span> %s"
                                       % (country_code, lang_name))
            map_lang_flag_list.append((lang_key, lang_html))

    map_language = forms.ChoiceField(choices=map_lang_flag_list,
                                     widget=forms.Select(
                                        attrs={'style': 'min-width: 200px'}))

    administrative_osmid = forms.IntegerField(widget=forms.HiddenInput,
                                              required=False)

    def __init__(self, *args, **kwargs):
        super(MapRenderingJobForm, self).__init__(*args, **kwargs)

        self._ocitysmap = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)

        layout_renderers = self._ocitysmap.get_all_renderers()
        stylesheets = self._ocitysmap.get_all_style_configurations()
        overlays = self._ocitysmap.get_all_overlay_configurations()

        self.fields['layout'].choices = []
        # TODO move descriptions to ocitysmap side
        for r in layout_renderers:
            if r.name == 'plain':
                description = _(u"Full-page layout without street index")
            elif r.name == 'single_page_index_side':
                description = _(u"Full-page layout with the street index on the side")
            elif r.name == 'single_page_index_bottom':
                description = _(u"Full-page layout with the street index at the bottom")
            elif r.name == 'single_page_index_extra_page':
                description = _(u"Full-page layout with the street index on extra page (PDF only)")
            elif r.name == 'tk25':
                description = _(u"TK25 full page layout")
            elif r.name == 'multi_page':
                description = _(u"Multi-page layout")
            else:
                continue
                # description = mark_safe(_(u"The %(layout_name)s layout") % {'layout_name':r.name})
            self.fields['layout'].choices.append((r.name, description))

        if not self.fields['layout'].initial:
            self.fields['layout'].initial = layout_renderers[0].name

        self.fields['indexer'].choices = [
            ('Street', 'Streets and selected amenities'),
            ('Health', 'Health related facilities'),
            ]

        if not self.fields['indexer'].initial:
            self.fields['indexer'].initial = 'Street' # TODO: make configurable

        style_choices = {"": []}
        for s in stylesheets:
            if s.description is not None:
                description = mark_safe(escape(s.description))
            else:
                description = mark_safe(_("The <i>%(stylesheet_name)s</i> stylesheet") % {'stylesheet_name':s.name})

            if s.url:
                description = mark_safe("%s <a target='_blank' href='%s' title='%s'><i class='fa fa-info-circle'></i></a>" % (description, s.url, _("more info")))

            if s.group:
                group = s.group
            else:
                group = ""

            if group not in style_choices:
                style_choices[group] = []
            style_choices[s.group].append((s.name, description))

        grouped_choices = []
        for name, members in style_choices.items():
            grouped_choices.append([name, members])
        self.fields['stylesheet'].choices = grouped_choices;

        if not self.fields['stylesheet'].initial:
            self.fields['stylesheet'].initial = stylesheets[0].name

        overlay_choices = {}
        for s in overlays:
            if s.description is not None:
                description = mark_safe(escape(s.description))
            else:
                description = mark_safe(_("The <i>%(stylesheet_name)s</i> overlay") % {'stylesheet_name':s.name})

            if s.url:
                description = mark_safe("%s <a target='_blank' href='%s' title='%s'><i class='fa fa-info-circle'></i></a>" % (description, s.url, _("more info")))

            if s.group not in overlay_choices:
                overlay_choices[s.group] = []
            overlay_choices[s.group].append((s.name, description))

        grouped_choices = []
        for name, members in overlay_choices.items():
            grouped_choices.append([name, members])
        self.fields['overlay'].choices = grouped_choices;

        if not self.fields['overlay'].initial:
            self.fields['overlay'].initial = ''

    def clean(self):
        """Cleanup function for the map query form. Different checks are
        required depending on the selected mode (by admininstrative city, or by
        bounding box).

        Returns the cleaned_data array.
        """

        cleaned_data = self.cleaned_data

        mode = cleaned_data.get("mode")
        city = cleaned_data.get("administrative_city")
        title = cleaned_data.get("maptitle")
        layout = cleaned_data.get("layout")
        indexer = cleaned_data.get("indexer")
        stylesheet = cleaned_data.get("stylesheet")
        overlay_array = []
        try:
            for overlay in cleaned_data.get("overlay"):
                overlay_array.append(overlay)
        except:
            pass
        overlay = ",".join(overlay_array)

        if layout == '':
            msg = _(u"Layout required")
            self._errors["layout"] = ErrorList([msg])
            del cleaned_data["layout"]

        if indexer == '':
            msg = _(u"Indexer required")
            self._errors["indexer"] = ErrorList([msg])
            del cleaned_data["indexer"]

        if stylesheet == '':
            msg = _(u"Stylesheet required")
            self._errors["stylesheet"] = ErrorList([msg])
            del cleaned_data["stylesheet"]

        if mode == 'admin':
            if city == "":
                msg = _(u"Administrative city required")
                self._errors["administrative_city"] = ErrorList([msg])
                del cleaned_data["administrative_city"]

            # Make sure that bbox and admin modes are exclusive
            # TODO: we should maybe merge these two instead? (See also OcitysMap Github Issue #24)
            cleaned_data["lat_upper_left"] = None
            cleaned_data["lon_upper_left"] = None
            cleaned_data["lat_bottom_right"] = None
            cleaned_data["lon_bottom_right"] = None

            try:
                self._check_osm_id(cleaned_data.get("administrative_osmid"))
            except Exception as ex:
                msg = _(u"Error with osm city: %s" % ex)
                self._errors['administrative_osmid'] \
                    = ErrorList([msg])

        elif mode == 'bbox':
            # Check bounding box corners are provided
            for f in [ "lat_upper_left", "lon_upper_left",
                       "lat_bottom_right", "lon_bottom_right" ]:
                val = cleaned_data.get(f)
                if val is None:
                    msg = _(u"Required")
                    self._errors['bbox'] = ErrorList([msg])
                    if f in cleaned_data:
                        del cleaned_data[f]

            # Check latitude and longitude are different
            if (cleaned_data.get("lat_upper_left")
                == cleaned_data.get("lat_bottom_right")):
                msg = _(u"Same latitude")
                self._errors['bbox'] = ErrorList([msg])
                del cleaned_data["lat_upper_left"]
                del cleaned_data["lat_bottom_right"]

            if (cleaned_data.get("lon_upper_left")
                == cleaned_data.get("lon_bottom_right")):
                msg = _(u"Same longitude")
                self._errors['bbox'] = ErrorList([msg])
                del cleaned_data["lon_upper_left"]
                del cleaned_data["lon_bottom_right"]

            # Make sure that bbox and admin modes are exclusive
            cleaned_data["administrative_city"] = ''
            cleaned_data["administrative_osmid"] = None

            # Don't try to instanciate a bounding box with empty coordinates
            if self._errors:
                return cleaned_data

            lat_upper_left = cleaned_data.get("lat_upper_left")
            lon_upper_left = cleaned_data.get("lon_upper_left")
            lat_bottom_right = cleaned_data.get("lat_bottom_right")
            lon_bottom_right = cleaned_data.get("lon_bottom_right")

            boundingbox = ocitysmap.coords.BoundingBox(
                lat_upper_left, lon_upper_left,
                lat_bottom_right, lon_bottom_right)
            (metric_size_lat, metric_size_long) = boundingbox.spheric_sizes()
            if (metric_size_lat > www.settings.BBOX_MAXIMUM_LENGTH_IN_METERS
                or metric_size_long > www.settings.BBOX_MAXIMUM_LENGTH_IN_METERS):
                msg = _(u"Bounding Box too large")
                self._errors['bbox'] = ErrorList([msg])

        return cleaned_data

    def _check_osm_id(self, osm_id):
        """Make sure that the supplied OSM Id is valid and can be accepted for
        rendering (bounding box not too large, etc.). Raise an exception in
        case of error."""
        bbox_wkt, area_wkt = self._ocitysmap.get_geographic_info(osm_id)
        bbox = ocitysmap.coords.BoundingBox.parse_wkt(bbox_wkt)
        (metric_size_lat, metric_size_long) = bbox.spheric_sizes()
        if metric_size_lat > www.settings.BBOX_MAXIMUM_LENGTH_IN_METERS or \
                metric_size_long > www.settings.BBOX_MAXIMUM_LENGTH_IN_METERS:
            raise ValueError("Area too large")


class MapPaperSizeForm(forms.Form):
    """
    The map paper size form, which is only used to analyze the
    arguments of the POST request to /apis/papersize/
    """
    osmid            = forms.IntegerField(required=False)
    layout           = forms.CharField(max_length=256)
    indexer          = forms.CharField(max_length=256)
    stylesheet       = forms.CharField(max_length=256)
    lat_upper_left   = forms.FloatField(required=False, min_value=-90.0, max_value=90.0)
    lon_upper_left   = forms.FloatField(required=False, min_value=-180.0, max_value=180.0)
    lat_bottom_right = forms.FloatField(required=False, min_value=-90.0, max_value=90.0)
    lon_bottom_right = forms.FloatField(required=False, min_value=-180.0, max_value=180.0)

class MapRecreateForm(forms.Form):
    """
    The map recreate form, to reschedule an already processed job on the queue.
    """

    id = forms.IntegerField(widget=forms.HiddenInput, required=True)

    def clean(self):
        cleaned_data = self.cleaned_data

        try:
            cleaned_data["id"] = int(cleaned_data.get("id", 0))
        except ValueError:
            cleaned_data["id"] = 0

        return cleaned_data

class MapCancelForm(forms.Form):
    """
    The map cancel form, to cancel a job (when the user has the matching
    nonce).
    """

    id = forms.IntegerField(widget=forms.HiddenInput, required=True)
    nonce = forms.CharField(widget=forms.HiddenInput, required=True)

    def clean(self):
        cleaned_data = self.cleaned_data

        try:
            cleaned_data["id"] = int(cleaned_data.get("id", 0))
        except ValueError:
            cleaned_data["id"] = 0

        return cleaned_data
