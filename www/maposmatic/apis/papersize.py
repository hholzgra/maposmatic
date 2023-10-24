# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2023  Hartmut Holzgraefe

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

import logging
LOG = logging.getLogger('maposmatic')

import json

from django.http import HttpResponse, HttpResponseBadRequest

import ocitysmap

import www.settings
from www.maposmatic import helpers, forms, nominatim, models

def api_papersize(request):
    """API handler to get the compatible paper sizes for the provided layout
    and bounding box."""

    if request.method != 'POST':
        return HttpResponseBadRequest("ERROR: Bad request")

    f = forms.MapPaperSizeForm(request.POST)
    if not f.is_valid():
        return HttpResponseBadRequest("ERROR: Invalid arguments")

    renderer = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)
    osmid = f.cleaned_data.get('osmid')
    layout = f.cleaned_data.get('layout')
    stylesheet = renderer.get_stylesheet_by_name(
        f.cleaned_data.get('stylesheet'))

    # Determine geographic area
    if osmid is not None:
        try:
            bbox_wkt, area_wkt = renderer.get_geographic_info(osmid)
        except ValueError:
            LOG.exception("Error determining compatible paper sizes")
            raise
        bbox = ocitysmap.coords.BoundingBox.parse_wkt(bbox_wkt)
    else:
        lat_upper_left = f.cleaned_data.get("lat_upper_left")
        lon_upper_left = f.cleaned_data.get("lon_upper_left")
        lat_bottom_right = f.cleaned_data.get("lat_bottom_right")
        lon_bottom_right = f.cleaned_data.get("lon_bottom_right")

        # Check we have correct floats
        if (lat_upper_left == None or lon_upper_left == None
            or lat_bottom_right == None or lon_bottom_right == None):
           return HttpResponseBadRequest("ERROR: Invalid arguments")

        bbox = ocitysmap.coords.BoundingBox(
            lat_upper_left, lon_upper_left,
            lat_bottom_right, lon_bottom_right)

    renderer_cls = ocitysmap.renderers.get_renderer_class_by_name(layout)

    paper_sizes = sorted(renderer_cls.get_compatible_paper_sizes(bbox, renderer),
                         key = lambda p: p['width'])

    return HttpResponse(content=json.dumps(paper_sizes),
                        content_type='text/json')

