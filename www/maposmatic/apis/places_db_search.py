# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2009  David Decotigny
# Copyright (C) 2009  Frédéric Lehobey
# Copyright (C) 2009  Pierre Mauduit
# Copyright (C) 2009  David Mentré
# Copyright (C) 2009  Maxime Petazzoni
# Copyright (C) 2009  Thomas Petazzoni
# Copyright (C) 2009  Gaël Utard
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

from django.http import HttpResponse, Http404
from django.db import connections
from django.db.transaction import TransactionManagementError
from django.utils.translation import gettext, gettext_lazy as _

import ocitysmap

import www.settings

def api_geosearch(request):
    """Simple place name search."""

    exclude = request.GET.get('exclude', '')
    squery = request.GET.get('q', '')
    squery = squery.lower()

    contents = { "entries": [] }

    cursor = None

    if www.settings.MAX_BOUNDING_BOX:
        m = www.settings.MAX_BOUNDING_BOX
        max_bbox = "ST_GeomFromText('POLYGON((%f %f, %f %f, %f %f, %f %f, %f %f))', 4326)" % (m[1], m[0], m[1], m[2], m[3], m[2], m[3], m[0], m[1], m[0])
        pt_bbox   = 'AND ST_Contains(ST_Transform(%s, 3857), pt.way)' % max_bbox
        poly_bbox = 'AND ST_Contains(ST_Transform(%s, 3857), poly.way)' % max_bbox
    else:
        pt_bbox   = ''
        poly_bbox = ''

    query =  """SELECT p.name
                     , p.display_name
                     , p.class
                     , p.type
                     , p.osm_type
                     , p.osm_id
                     , p.lat
                     , p.lon
                     , p.west
                     , p.east
                     , p.north
                     , p.south
                     , p.place_rank
                     , p.importance
                     , p.country_code
                  FROM place p
             LEFT JOIN planet_osm_hstore_point pt
                    ON p.osm_id = pt.osm_id
                    %s -- optionally filter by max bbox
             LEFT JOIN planet_osm_hstore_polygon poly
                    ON - p.osm_id = poly.osm_id
                    %s -- optionally filter by max bbox
                 WHERE LOWER(p.name) = %%s
                   AND (  pt.osm_id IS NOT NULL
                       OR poly.osm_id IS NOT NULL
                       )
              ORDER BY p.place_rank
                     , p.importance DESC
            """ % (pt_bbox, poly_bbox)

    try:
        cursor = connections['osm'].cursor()
        if cursor is None:
            raise Http404("postgis: no cursor")

        cursor.execute(query, [ squery ])

        columns = [col[0] for col in cursor.description]

        for row in cursor.fetchall():
            values = dict(zip(columns, row))

            values["boundingbox"] = "%f,%f,%f,%f" % (values["south"], values["north"], values["west"], values["east"])
            bbox = ocitysmap.coords.BoundingBox(values["south"], values["west"], values["north"], values["east"])
            (metric_size_lat, metric_size_lon) = bbox.spheric_sizes()
            LOG.warning("metric lat/lon %f : %f - %f" %  (metric_size_lat, metric_size_lon, www.settings.BBOX_MAXIMUM_LENGTH_IN_METERS))

            if values["osm_type"] == "node":
                values["icon"] = "../media/img/place-node.png"
                values["ocitysmap_params"] = {
                    "valid": False,
                    "reason": "no-admin",
                    "reason_text": "No administrative boundary"
                }
            else:
                values["icon"] = "../media/img/place-polygon.png"
                if (metric_size_lat > www.settings.BBOX_MAXIMUM_LENGTH_IN_METERS
                    or metric_size_lon > www.settings.BBOX_MAXIMUM_LENGTH_IN_METERS):
                    valid = False
                    reason = "area-too-big"
                    reason_text = gettext("Administrative area too big for rendering")
                else:
                    valid = True
                    reason = ""
                    reason_text = ""

                values["ocitysmap_params"] = {
                    "valid": valid,
                    "table": "polygon",
                    "id": -values["osm_id"],
                    "reason": reason,
                    "reason_text": reason_text
                }

            contents["entries"].append(values)

        cursor.close()

        return HttpResponse(content=json.dumps(contents),
                            content_type='text/json')

    except Exception as e:
        raise TransactionManagementError(e)

