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


def api_polygon(request, osm_id):
    """API handler that returns the polygon outline from an OSM ID polygon."""

    try:
        osm_id = int(osm_id)
    except ValueError:
        return HttpResponseBadRequest("ERROR: Invalid arguments")

    renderer = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)
    try:
        bbox_wkt, area_wkt = renderer.get_geographic_info(osm_id)
        bbox = ocitysmap.coords.BoundingBox.parse_wkt(bbox_wkt).as_json_bounds()
        return HttpResponse(content=json.dumps({'bbox': bbox, 'wkt': area_wkt}),
                            content_type='text/json')
    except:
        LOG.exception("Error retrieving polygon outline for OSM ID %d!" % osm_id)

    return HttpResponseBadRequest("ERROR: OSM ID %d not found!" % osm_id)
