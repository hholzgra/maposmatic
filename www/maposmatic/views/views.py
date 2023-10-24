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

# Views for MapOSMatic

import datetime
import logging
import json
import os

from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound, HttpResponse, Http404
from django.db.transaction import TransactionManagementError
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext
from django.utils.translation import gettext, gettext_lazy as _
from django.core import serializers
from django.forms.models import model_to_dict
from django.core.exceptions import ValidationError
from django.urls import get_script_prefix
from django.db import connections
from django.utils.safestring import mark_safe

import ocitysmap
from www.maposmatic import helpers, forms, nominatim, models
import www.settings

import psycopg2


LOG = logging.getLogger('maposmatic')


def congo(request):
    """The congo health map page."""
    return render(request,
                  'maposmatic/congo.html',
                  { }
                 )




def create_upload_file(job, file, keep_until = None):
    first_line = file.readline().decode("utf-8-sig")
    LOG.info("firstline type %s" % type(first_line))
    if first_line.startswith(u'<?xml'):
        file_type = 'gpx'
    else:
        file_type = 'umap'
    file_instance =  models.UploadFile(uploaded_file = file,
                                       file_type = file_type,
                                       keep_until = keep_until)
    file_instance.save()
    file_instance.job.add(job)

def cancel(request):
    if request.method == 'POST':
        form = forms.MapCancelForm(request.POST)
        if form.is_valid():
            job = get_object_or_404(models.MapRenderingJob,
                                    id=form.cleaned_data['id'],
                                    nonce=form.cleaned_data['nonce'])
            job.cancel()

            return HttpResponseRedirect(reverse('map-by-id-and-nonce',
                                                args=[job.id, job.nonce]))

    return HttpResponseBadRequest("ERROR: Invalid request")

def api_nominatim(request):
    """Nominatim query gateway."""
    exclude = request.GET.get('exclude', '')
    squery = request.GET.get('q', '')
    lang = None

    if 'HTTP_ACCEPT_LANGUAGE' in request.META:
        # Accept-Language headers typically look like
        # fr,fr-fr;q=0.8,en-us;q=0.5,en;q=0.3. Unfortunately,
        # Nominatim behaves improperly with such a string: it gives
        # the region name in French, but the country name in
        # English. We split at the first comma to only keep the
        # preferred language, which makes Nominatim work properly.
        lang = request.META['HTTP_ACCEPT_LANGUAGE'].split(',')[0]

    try:
        contents = nominatim.query(squery, exclude, with_polygons=False,
                accept_language=lang)
    except Exception as e:
        LOG.exception("Error querying Nominatim")
        contents = []

    return HttpResponse(content=json.dumps(contents),
                        content_type='text/json')

def heatmap(request, days=7):
    return render(request, 'maposmatic/heatmap.html',
                  { 'days' : days ,
                  })


def api_nominatim_reverse(request, lat, lon):
    """Nominatim reverse geocoding query gateway."""
    lat = float(lat)
    lon = float(lon)
    return HttpResponse(json.dumps(nominatim.reverse_geo(lat, lon)),
                        content_type='text/json')

def api_postgis_reverse(request, lat, lon):
    lat = float(lat)
    lon = float(lon)
    cursor = None
    query = """select country_code
                 from country_osm_grid
                where st_contains(geometry,
                                  st_geomfromtext('POINT(%f %f)', 4326))
            """ % (lon, lat)

    LOG.debug("Reverse Lookup Query %s" % query)

    try:
        connections['osm'].rollback() # make sure there's no pending transaction
        cursor = connections['osm'].cursor()

        cursor.execute(query)
        country_code = cursor.fetchone()
        cursor.close()
        if country_code is None or len(country_code) < 1:
            raise Http404("postgis: country not found")

        return HttpResponse('{"address": {"country_code": "%s"}}' % country_code[0], content_type='text/json')
    except Exception as e:
        LOG.warning("reverse geo lookup failed: %s" % e)
        pass
    finally:
        # Close the DB cursor if necessary
        if cursor is not None and not cursor.closed:
            cursor.close()

    raise Http404("postgis: something went wrong")

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


def api_rendering_status(request, id, nonce=None):
    """API handler for updating map request rendering status"""

    try:
        id = int(id)
    except ValueError:
        return HttpResponseBadRequest("ERROR: Invalid arguments")

    job = get_object_or_404(models.MapRenderingJob, id=id)
    isredirected = request.session.get('redirected', False)
    request.session.pop('redirected', None)

    queue_size = job.index_queue_at_submission
    progress = 100
    if queue_size:
       progress = int(100 * (queue_size -
           job.current_position_in_queue()) / float(queue_size))

    refresh = job.is_rendering() and \
        www.settings.REFRESH_JOB_RENDERING or \
        www.settings.REFRESH_JOB_WAITING

    return render(request, 'maposmatic/map-full-parts/rendering-status.html',
                              { 'map':        job,
                                'redirected': isredirected,
                                'nonce':      nonce,
                                'refresh':    refresh,
                                'progress':   progress,
                                'queue_size': queue_size,
                                'status':     job.renderstep or "working",
                              })
