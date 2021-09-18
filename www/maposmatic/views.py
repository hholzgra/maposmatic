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
from django.shortcuts import get_object_or_404, render_to_response, render
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _
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

def index(request):
    """The main page."""
    form = forms.MapSearchForm(request.GET)

    job_list = (models.MapRenderingJob.objects.all()
                .order_by('-submission_time'))
    job_list = (job_list.filter(status=0) |
                job_list.filter(status=1))

    return render(request,
                  'maposmatic/index.html',
                  { 'form': form,
                    'queued': job_list.count()
                  }
                 )

def about(request):
    """The about page."""
    form = forms.MapSearchForm(request.GET)

    job_list = (models.MapRenderingJob.objects.all()
                .order_by('-submission_time'))
    job_list = (job_list.filter(status=0) |
                job_list.filter(status=1))

    return render(request,
                  'maposmatic/about.html',
                  { 'form': form,
                    'queued': job_list.count()
                  }
                 )

def privacy(request):
    """The privacy statement page."""
    return render(request,
                  'maposmatic/privacy.html',
                  { }
                 )

def documentation_user_guide(request):
    """The user guide page."""
    return render(request,
                  'maposmatic/documentation-user-guide.html',
                  { }
                 )

def documentation_api(request):
    """The api documentation."""
    return render(request,
                  'maposmatic/documentation-api.html',
                  { }
                 )


def donate(request):
    """The donate page."""
    form = forms.MapSearchForm(request.GET)

    job_list = (models.MapRenderingJob.objects.all()
                .order_by('-submission_time'))
    job_list = (job_list.filter(status=0) |
                job_list.filter(status=1))

    return render(request,
                  'maposmatic/donate.html',
                  { 'form': form,
                    'queued': job_list.count()
                  }
                 )

def donate_thanks(request):
    """The thanks for donation page."""
    return render_to_response('maposmatic/donate-thanks.html')

def create_upload_file(job, file):
    first_line = file.readline().decode("utf-8-sig")
    LOG.info("firstline type %s" % type(first_line))
    if first_line.startswith(u'<?xml'):
        file_type = 'gpx'
    else:
        file_type = 'umap'
    file_instance =  models.UploadFile(uploaded_file = file, file_type = file_type)
    file_instance.save()
    file_instance.job.add(job)

def new(request):
    """The map creation page and form."""

    papersize_buttons = ''

    if request.method == 'POST':
        form = forms.MapRenderingJobForm(request.POST, request.FILES)
        if form.is_valid():
            request.session['new_layout'] = form.cleaned_data.get('layout')
            request.session['new_stylesheet'] = form.cleaned_data.get('stylesheet')
            request.session['new_overlay'] = form.cleaned_data.get('overlay')
            request.session['new_paper_width_mm'] = form.cleaned_data.get('paper_width_mm')
            request.session['new_paper_height_mm'] = form.cleaned_data.get('paper_height_mm')

            job = form.save(commit=False)
            job.administrative_osmid = form.cleaned_data.get('administrative_osmid')
            job.stylesheet = form.cleaned_data.get('stylesheet')
            job.overlay = ",".join(form.cleaned_data.get('overlay'))
            job.layout = form.cleaned_data.get('layout')
            job.paper_width_mm = form.cleaned_data.get('paper_width_mm')
            job.paper_height_mm = form.cleaned_data.get('paper_height_mm')
            job.status = 0 # Submitted
            if www.settings.SUBMITTER_IP_LIFETIME != 0:
                job.submitterip = request.META['REMOTE_ADDR']
            else:
                job.submitterip = None

            job.submitteremail = form.cleaned_data.get('submitteremail')
            job.map_language = form.cleaned_data.get('map_language')
            job.index_queue_at_submission = (models.MapRenderingJob.objects
                                             .queue_size())
            job.nonce = helpers.generate_nonce(models.MapRenderingJob.NONCE_SIZE)

            job.save()

            files = request.FILES.getlist('uploadfile')
            for file in files:
                create_upload_file(job, file)

            return HttpResponseRedirect(reverse('map-by-id-and-nonce',
                                                args=[job.id, job.nonce]))
        else:
            LOG.debug("FORM NOT VALID")
    else:
        init_vals = request.GET.dict()
        oc = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)

        if not 'layout' in init_vals and 'new_layout' in request.session :
            init_vals['layout'] = request.session['new_layout']
        else:
           request.session['new_layout'] = oc.get_all_renderer_names()[0]

        if not 'stylesheet' in init_vals and 'new_stylesheet' in request.session:
            init_vals['stylesheet'] = request.session['new_stylesheet']
        else:
            request.session['new_stylesheet'] = oc.get_all_style_names()[0]

        if not 'overlay' in init_vals and 'new_overlay' in request.session:
            init_vals['overlay'] = request.session['new_overlay']

        if not 'paper_width_mm' in init_vals and 'new_paper_width_mm' in request.session:
            init_vals['paper_width_mm'] = request.session['new_paper_width_mm']

        if not 'paper_height_mm' in init_vals and 'new_paper_width_mm' in request.session:
            init_vals['paper_height_mm'] = request.session['new_paper_height_mm']

        form = forms.MapRenderingJobForm(initial=init_vals)

        _ocitysmap = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)

        # TODO: create tempates for these button lines ...
        papersize_buttons += "<p><button id='paper_best_fit' type='button' class='btn btn-primary papersize papersize_best_fit' onclick='set_papersize(0,0);'><i class='fas fa-square fa-2x'></i></button> <b>Best fit</b> (<span id='best_width'>?</span>&times;<span id='best_height'>?</span>mm²)</p>"
        for p in _ocitysmap.get_all_paper_sizes():
            if p[1] is not None:
                papersize_buttons += "<p>"
                if p[1] != p[2]:
                    papersize_buttons += "<button id='paper_{0}_{1}' type='button' class='btn btn-primary papersize papersize_{0}_{1}' onclick='set_papersize({0}, {1});'><i class='fas fa-portrait fa-2x'></i></button> ".format(p[1], p[2])
                    papersize_buttons += "<button id='paper_{0}_{1}' type='button' class='btn btn-primary papersize papersize_{0}_{1}' onclick='set_papersize({0}, {1});'><i class='fas fa-image fa-2x'></i></button> ".format(p[2], p[1])
                else:
                    papersize_buttons += "<button id='paper_{0}_{1}' disabled type='button' class='btn btn-primary papersize papersize_{0}_{1}' onclick='set_papersize({0}, {1});'><i class='fas fa-square fa-2x'></i></button> ".format(p[1], p[2])

                papersize_buttons += "<b>%s</b> (%s&times;%smm²)</p>" % (p[0], repr(p[1]), repr(p[2]))

        multisize_buttons = ''
        for p in _ocitysmap.get_all_paper_sizes('multipage'):
            if p[1] is not None:
                multisize_buttons += "<p>"
                if p[1] != p[2]:
                    multisize_buttons += "<button id='multipaper_{0}_{1}' type='button' class='btn btn-primary papersize papersize_{0}_{1}' onclick='set_papersize({0}, {1});'><i class='fas fa-portrait fa-2x'></i></button> ".format(p[1], p[2])
                    multisize_buttons += "<button id='multipaper_{0}_{1}' type='button' class='btn btn-primary papersize papersize_{0}_{1}' onclick='set_papersize({0}, {1});'><i class='fas fa-image fa-2x'></i></button> ".format(p[2], p[1])
                else:
                    multisize_buttons += "<button id='multipaper_{0}_{1}' disabled type='button' class='btn btn-primary papersize papersize_{0}_{1}' onclick='set_papersize({0}, {1});'><i class='fas fa-square fa-2x'></i></button> ".format(p[1], p[2])
                multisize_buttons += "<b>%s</b> (%s&times;%smm²)</p>" % (p[0], repr(p[1]), repr(p[2]))

        return render(request, 'maposmatic/new.html',
                      { 'form' : form ,
                        'papersize_suggestions': mark_safe(papersize_buttons),
                        'multipage_papersize_suggestions': mark_safe(multisize_buttons),
                      })

def map_full(request, id, nonce=None):
    """The full-page map details page.

    Args:
        id (int): the job ID in the database.
    """

    job = get_object_or_404(models.MapRenderingJob, id=id)
    isredirected = request.session.get('redirected', False)
    request.session.pop('redirected', None)

    queue_size = models.MapRenderingJob.objects.queue_size()
    progress = 100
    if queue_size:
        progress = 20 + int(80 * (queue_size -
            job.current_position_in_queue()) / float(queue_size))

    refresh = job.is_rendering() and \
        www.settings.REFRESH_JOB_RENDERING or \
        www.settings.REFRESH_JOB_WAITING

    return render(request, 'maposmatic/map-full.html',
                              { 'map': job, 'redirected': isredirected,
                                'nonce': nonce, 'refresh': refresh,
                                'progress': progress, 'queue_size': queue_size })

def maps(request, category=None):
    """Displays all maps and jobs, sorted by submission time, or maps matching
    the search terms when provided."""

    map_list = None

    form = forms.MapSearchForm(request.GET)
    if form.is_valid():
        map_list = (models.MapRenderingJob.objects
                    .order_by('-submission_time')
                    .filter(maptitle__icontains=form.cleaned_data['query']))
        if len(map_list) == 1:
            return HttpResponseRedirect(reverse('map-by-id',
                                                args=[map_list[0].id]))
    else:
        form = forms.MapSearchForm()

    if map_list is None:
        map_list = (models.MapRenderingJob.objects
                    .order_by('-submission_time'))
        if category == 'errors':
            map_list = map_list.filter(status=2).exclude(resultmsg='ok')

    paginator = Paginator(map_list, www.settings.ITEMS_PER_PAGE)

    try:
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1

        maps = paginator.page(page)
    except (EmptyPage, InvalidPage):
        maps = paginator.page(paginator.num_pages)

    return render(request, 'maposmatic/maps.html',
                              { 'maps': maps, 'form': form,
                                'is_search': form.is_valid(),
                                'pages': helpers.get_pages_list(maps, paginator) })


def recreate(request):
    if request.method == 'POST':
        form = forms.MapRecreateForm(request.POST)
        if form.is_valid():
            job = get_object_or_404(models.MapRenderingJob,
                                    id=form.cleaned_data['id'])

            newjob = models.MapRenderingJob()
            newjob.maptitle = job.maptitle

            newjob.administrative_city = job.administrative_city
            newjob.administrative_osmid = job.administrative_osmid

            newjob.lat_upper_left = job.lat_upper_left
            newjob.lon_upper_left = job.lon_upper_left
            newjob.lat_bottom_right = job.lat_bottom_right
            newjob.lon_bottom_right = job.lon_bottom_right

            newjob.stylesheet = job.stylesheet
            newjob.overlay = job.overlay
            newjob.layout = job.layout
            newjob.paper_width_mm = job.paper_width_mm
            newjob.paper_height_mm = job.paper_height_mm

            newjob.status = 0 # Submitted
            if www.settings.SUBMITTER_IP_LIFETIME != 0:
                newjob.submitterip = request.META['REMOTE_ADDR']
            else:
                newjob.submitterip = None
            newjob.submittermail = None # TODO
            newjob.map_language = job.map_language
            newjob.index_queue_at_submission = (models.MapRenderingJob.objects
                                               .queue_size())
            newjob.nonce = helpers.generate_nonce(models.MapRenderingJob.NONCE_SIZE)

            newjob.save()

            for each in job.uploads.all():
                each.job.add(newjob)

            return HttpResponseRedirect(reverse('map-by-id-and-nonce',
                                                args=[newjob.id, newjob.nonce]))

    return HttpResponseBadRequest("ERROR: Invalid request")

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
                    reason_text = ugettext("Administrative area too big for rendering")
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

def api_bbox(request, osm_id):
    """API handler that returns the bounding box from an OSM ID polygon."""

    try:
        osm_id = int(osm_id)
    except ValueError:
        return HttpResponseBadRequest("ERROR: Invalid arguments")

    renderer = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)
    try:
        bbox_wkt, area_wkt = renderer.get_geographic_info(osm_id)
        bbox = ocitysmap.coords.BoundingBox.parse_wkt(bbox_wkt)
        return HttpResponse(content=json.dumps(bbox.as_json_bounds()),
                            content_type='text/json')
    except:
        LOG.exception("Error calculating bounding box for OSM ID %d!" % osm_id)

    return HttpResponseBadRequest("ERROR: OSM ID %d not found!" % osm_id)

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

def api_rendering_status(request, id, nonce=None):
    """API handler for updating map request rendering status"""

    try:
        id = int(id)
    except ValueError:
        return HttpResponseBadRequest("ERROR: Invalid arguments")

    job = get_object_or_404(models.MapRenderingJob, id=id)
    isredirected = request.session.get('redirected', False)
    request.session.pop('redirected', None)

    queue_size = models.MapRenderingJob.objects.queue_size()
    progress = 100
    if queue_size:
        progress = 20 + int(80 * (queue_size -
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
                                'status':     'working'
                              })
