# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2024  Hartmut Holzgraefe

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

import www.settings

from django import forms
from django.forms.utils import ErrorList
from django.utils.translation import get_language, gettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.html import escape

from www.maposmatic import models, widgets

import ocitysmap

from multiupload.fields import MultiFileField


class MapRenderingJobForm(forms.ModelForm):
    """
    The main map rendering form, displayed on the 'Create Map' page. It's a
    ModelForm based on the MapRenderingJob model.
    """
    class Meta:
        model = models.MapRenderingJob
        fields = ('layout',
                  'indexer',
                  'stylesheet',
                  'overlay',
                  'maptitle',
                  'administrative_city',
                  'lat_upper_left',
                  'lon_upper_left',
                  'lat_bottom_right',
                  'lon_bottom_right',
                  'submittermail',
                  )

    mode            = forms.CharField(initial='bbox',
                                      widget=forms.HiddenInput,
                                      )
    layout          = forms.ChoiceField(choices=(),
                                        widget=forms
                                        .Select(attrs= { 'onchange' : 'clearPaperSize(this.value); load_preview("#layout-preview", this.value); indexer_visible(this.value);'}))
    indexer         = forms.ChoiceField(choices=(),
                                        widget=forms.Select())
    stylesheet      = forms.ChoiceField(choices=(),
                                        widget=forms.Select(attrs= { 'onchange' : '$("#style-preview").attr("src","/media/img/style/"+this.value+".jpg");'}))
    overlay         = forms.MultipleChoiceField(choices=(),
                                                widget=forms.SelectMultiple(attrs= { 'class': 'multipleSelect' }),
                                                required=False)
    paper_width_mm  = forms.IntegerField(widget=forms.NumberInput(attrs= { 'onchange' : 'change_papersize();',
                                                                           'style':     'width: 5em;',
                                                                          }),
                                         min_value=www.settings.PAPER_WIDTH_MIN,
                                         max_value=www.settings.PAPER_WIDTH_MAX,
                                         )
    paper_height_mm = forms.IntegerField(widget=forms.NumberInput(attrs= { 'onchange' : 'change_papersize();',
                                                                           'style':     'width: 5em;',
                                                                          }),
                                         min_value=www.settings.PAPER_HEIGHT_MIN,
                                         max_value=www.settings.PAPER_HEIGHT_MAX,
                                         )
    maptitle        = forms.CharField(max_length=256,
                                      required=False,
                                      )
    bbox            = widgets.AreaField(label=_("Area"),
                                        fields=(forms.FloatField(),
                                                forms.FloatField(),
                                                forms.FloatField(),
                                                forms.FloatField()
                                                )
                                        )
    uploadfile      = MultiFileField(required=False)

    delete_files_after_rendering = forms.BooleanField(required=False)

    map_lang_flag_list = []
    for lang_key, lang_name in www.settings.MAP_LANGUAGES_LIST:
        if lang_key == 'C':
            map_lang_flag_list.append((lang_key, lang_name))
        else:
            country_code = lang_key[3:5].lower()
            lang_html = mark_safe("<span class='fi fi-%s'> </span> %s"
                                       % (country_code, lang_name))
            map_lang_flag_list.append((lang_key, lang_html))

        map_language = forms.ChoiceField(choices=map_lang_flag_list,
                                         widget=forms.Select(
                                             attrs={'style': 'min-width: 200px'},
                                         ))

    administrative_osmid = forms.IntegerField(widget=forms.HiddenInput,
                                              required=False,
                                              )

    def __init__(self, *args, **kwargs):
        super(MapRenderingJobForm, self).__init__(*args, **kwargs)

        self._ocitysmap = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH, get_language())

        layout_renderers = self._ocitysmap.get_all_renderers()
        indexers         = self._ocitysmap.get_all_indexers()
        stylesheets      = self._ocitysmap.get_all_style_configurations()
        overlays         = self._ocitysmap.get_all_overlay_configurations()

        self.fields['layout'].choices = []
        # TODO move descriptions to ocitysmap side
        for r in layout_renderers:
            self.fields['layout'].choices.append((r.name, self._ocitysmap.translate(r.description)))

        if not self.fields['layout'].initial:
            self.fields['layout'].initial = layout_renderers[0].name

        # TODO get these from ocitysmap instead of hardcoding here
        self.fields['indexer'].choices = self._ocitysmap.get_all_indexers_name_desc()

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

        data = self.cleaned_data

        mode          = data.get("mode")
        city          = data.get("administrative_city")
        title         = data.get("maptitle")
        layout        = data.get("layout")
        indexer       = data.get("indexer")
        stylesheet    = data.get("stylesheet")
        overlay_array = []
        try:
            for overlay in data.get("overlay"):
                overlay_array.append(overlay)
        except:
            pass
        overlay = ",".join(overlay_array)

        if layout == '':
            msg = _(u"Layout required")
            self._errors["layout"] = ErrorList([msg])

        if indexer == '':
            msg = _(u"Indexer required")
            self._errors["indexer"] = ErrorList([msg])

        if stylesheet == '':
            msg = _(u"Stylesheet required")
            self._errors["stylesheet"] = ErrorList([msg])

        if mode == 'admin':
            # TODO as bounding box override now exists (Issue #24)
            #      we need to do the same bbox checks here as in
            #      the mode=bbox section below?
            if city == "":
                msg = _(u"Administrative city required")
                self._errors["administrative_city"] = ErrorList([msg])

            try:
                self._check_osm_id(data.get("administrative_osmid"))
            except Exception as ex:
                msg = _(u"Error with osm city: %s" % ex)
                self._errors['administrative_osmid'] \
                    = ErrorList([msg])

        elif mode == 'bbox':
            msgs = []

            # Check bounding box corners are provided
            for f in [ "lat_upper_left", "lon_upper_left",
                       "lat_bottom_right", "lon_bottom_right"]:
                if not f in data:
                    msgs.append(_(u"Required field '%s' missing") % f)

            # Check latitude and longitude are different
            # TODO: relax this as auto-extend can deal with zero width OR height?
            #       and even both being zero could be handled by having a min. width/height?
            if (data.get("lat_upper_left") == data.get("lat_bottom_right")):
                msgs.append(_(u"Same latitude"))

            if (data.get("lon_upper_left") == data.get("lon_bottom_right")):
                msgs.append(_(u"Same longitude"))

            # Make sure that bbox and admin modes are exclusive
            data["administrative_city"] = ''
            data["administrative_osmid"] = None

            # Don't try to instanciate a bounding box with empty coordinates
            if len(msgs):
                self._errors['bbox'] = ErrorList(msgs)
                return data

            lat_upper_left = data.get("lat_upper_left")
            lon_upper_left = data.get("lon_upper_left")
            lat_bottom_right = data.get("lat_bottom_right")
            lon_bottom_right = data.get("lon_bottom_right")

            boundingbox = ocitysmap.coords.BoundingBox(
                lat_upper_left, lon_upper_left,
                lat_bottom_right, lon_bottom_right)

            (metric_size_lat, metric_size_long) = boundingbox.spheric_sizes()
            if (metric_size_lat > www.settings.BBOX_MAXIMUM_LENGTH_IN_METERS
                or metric_size_long > www.settings.BBOX_MAXIMUM_LENGTH_IN_METERS):
                self._errors['bbox'] = ErrorList([_(u"Bounding Box too large")])

        return data

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
