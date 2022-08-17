# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2018  Hartmut Holzgraefe

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

# API calls for MapOSMatic

from os import path

import json

from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.base import ContentFile
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound, HttpResponse, HttpResponseNotAllowed, Http404
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from django.db import connections

import ocitysmap
from www.maposmatic import helpers, forms, nominatim, models
import www.settings

import gpxpy
import gpxpy.gpx

import requests
from tempfile import NamedTemporaryFile
import urllib.parse

import logging
LOG = logging.getLogger('maposmatic')


def styles(request):
    result = {}
    for style in ocitysmap.OCitySMap().get_all_style_configurations():
        result[style.name] = { "description": style.description, 
                               "annotation": style.annotation,
                               "preview_url": request.build_absolute_uri('/media/img/style/'+style.name+'.png')
                             }

    return HttpResponse( content=json.dumps(result, indent=4, sort_keys=True, default=str), content_type='text/json')



def overlays(request):
    result = {}
    for overlay in ocitysmap.OCitySMap().get_all_overlay_configurations():
        result[overlay.name] = { "description": overlay.description, 
                                 "annotation": overlay.annotation,
                                 "preview_url": request.build_absolute_uri('/media/img/overlay/'+overlay.name+'.png')
                               }

    return HttpResponse( content=json.dumps(result, indent=4, sort_keys=True, default=str), content_type='text/json')



def paper_formats(request):
    _ocitysmap = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)
    
    result = {}
    for p in _ocitysmap.get_all_paper_sizes():
        if p[1] and p[2]:
            result[p[0]] = {'width': p[1], 'height': p[2]}

    return HttpResponse( content=json.dumps(result, indent=4, sort_keys=True, default=str), content_type='text/json')



def layouts(request):
    result = {}
    for renderer in ocitysmap.OCitySMap().get_all_renderers():
        result[renderer.name] = { "description": renderer.description,
                                  "preview_url": request.build_absolute_uri('/media/img/layout/'+renderer.name+'.png')
                         }

    return HttpResponse( content=json.dumps(result, indent=4, sort_keys=True, default=str), content_type='text/json')

def job_stati_dict(id = None):
    # TODO do not hard-code these, get them from OCitysMap cleanly
    result = {
        "0": "Submitted",
        "1": "In progress",
        "2": "Done",
        "3": "Done w/o files",
        "4": "Cancelled"
    }

    if id is not None:
        return result[str(id)]

    return result


def job_stati(request):
    return HttpResponse( content=json.dumps(job_stati_dict(), indent=4, sort_keys=True, default=str), content_type='text/json')

def heatdata(request):
    query = """
select (lat_upper_left + lat_bottom_right)/2 as lat
     , (lon_upper_left + lon_bottom_right)/2 as lng
     , 1 as count
  from maposmatic_maprenderingjob
 where lat_upper_left is not null
"""

    data = { "max": 8, "data": [] }
    
    try:
        cursor = connections['default'].cursor()
        if cursor is None:
            raise Http404("postgis: no cursor")

        cursor.execute(query)

        columns = [col[0] for col in cursor.description]

        for row in cursor.fetchall():
            data["data"].append(dict(zip(columns, row)))

        cursor.close()

        return HttpResponse(content="var data = " + json.dumps(data),
                            content_type='application/javascript')

    except Exception as e:
        raise RuntimeError(e)

    
def jobs(request, job_id=False):
    """API handler for external rendering requests"""

    if request.method == 'GET':
        return _jobs_get(request, job_id)
    elif request.method == 'POST':
        return _jobs_post(request)
    else:
        return HttpResponseNotAllowed(['GET','POST'])

def _jobs_get(request, job_id):
    if not job_id:
        return HttpResponseNotFound('not found')

    job = get_object_or_404(models.MapRenderingJob, id=job_id)

    reply = model_to_dict(job)

    result = {}
    result['id']              = int(job_id)
    result['status']          = reply['status']
    result['status_msg']      = job_stati_dict(reply['status'])

    if reply['administrative_osmid']:
        result['osm_id']      = reply['administrative_osmid']
    else:
        result['bbox_top']    = reply['lat_upper_left']
        result['bbox_bottom'] = reply['lat_bottom_right']
        result['bbox_left']   = reply['lon_upper_left']
        result['bbox_right']  = reply['lon_bottom_right']

    result['title']           = reply['maptitle']
    result['layout']          = reply['layout']
    result['style']           = reply['stylesheet']

    if reply['overlay']:
        result['overlays']    = reply['overlay'].split(',')

    result['language']        = reply['map_language']
    result['paper_height_mm'] = reply['paper_height_mm']
    result['paper_width_mm']  = reply['paper_width_mm']

    if job.status == 0:
        result['queue_size'] = models.MapRenderingJob.objects.queue_size()
    else:
        result['queue_size'] = 0

    result['files'] = {}
    if job.status == 2:
        files = job.output_files()
        for key, val in files['maps'].items():
            result['files'][key] = request.build_absolute_uri(val[0])

    result['interactive']     = request.build_absolute_uri('../../../maps/%d' % reply['id'])

    if job.status <= 1:
        status = 202
    else:
        status = 200

    return HttpResponse( content=json.dumps(result, indent=4, sort_keys=True, default=str)
                       , content_type='text/json', status=status)



def _jobs_post(request):
    result = { "error": {} }

    job = models.MapRenderingJob()

    if request.content_type == 'application/json':
        input = json.loads(request.body.decode('utf-8-sig'))
    else:
        input = json.loads(request.POST['job'])

    valid_keys = ['osmid',
                  'bbox',
                  'bbox_bottom',
                  'bbox_left',
                  'bbox_right',
                  'bbox_top',
                  'min_lat',
                  'max_lat',
                  'min_lon',
                  'max_lon',
                  'import_urls',
                  'language',
                  'layout',
                  'orientation',
                  'overlays',
                  'paper_height',
                  'paper_size',
                  'paper_width',
                  'style',
                  'title',
                  'track_url',
                  'umap_url'
    ]

    for key in input:
        if key not in valid_keys:
            result['error'][key] = "Unknown parameter '%s'" % key

    if 'osmid' in input:
        job.administrative_osmid= input['osmid']
    elif 'bbox' in input:
        job.lat_upper_left   = input['bbox'][0]
        job.lon_upper_left   = input['bbox'][3]
        job.lat_bottom_right = input['bbox'][2]
        job.lon_bottom_right = input['bbox'][1]
    elif 'lat_min' in input and 'lat_max' in input and 'lon_min' in input and 'lon_max' in input: 
        job.lat_upper_left   = input['max_lat']
        job.lon_upper_left   = input['min_lon']
        job.lat_bottom_right = input['min_lat']
        job.lon_bottom_right = input['max_lon']
    elif 'bbox_top' in input and 'bbox_bottom' in input and 'bbox_left' in input and 'bbox_right' in input:
        job.lat_upper_left   = input['bbox_top']
        job.lon_upper_left   = input['bbox_left']
        job.lat_bottom_right = input['bbox_bottom']
        job.lon_bottom_right = input['bbox_right']

    if 'title' in input:
        job.maptitle = input['title']

    if 'language' in input:
        job.map_language = input['language']
    else:
        job.map_language = 'en_US.UTF-8'

    if 'layout' in input:
        job.layout = input['layout']

    if 'style' in input:
        job.stylesheet = input['style']
    else:
        job.stylesheet = 'CartoOSM'

    if 'overlays' in input:
        if isinstance(input['overlays'], str):
            job.overlay = input['overlays']
        else:
            job.overlay = ",".join(input['overlays'])

    job.paper_width_mm  = 210
    job.paper_height_mm = 297

    # TODO: either both or none of width/height need to be set
    # TODO: size and width/height are mutually exclusive
    if 'paper_width' in input:
        job.paper_width_mm = input['paper_width']
    if 'paper_height' in input:
        job.paper_height_mm = input['paper_height']
    if 'paper_size' in input:
        try:
            _ocitysmap = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)
            p = _ocitysmap.get_paper_size_by_name(input['paper_size'])
            if 'orientation' in input:
                if input['orientation'] == 'landscape':
                    p[1], p[0] = p[0], p[1]
            job.paper_width_mm  = p[0]
            job.paper_height_mm = p[1]
        except LookupError as e:
            result['error']['paper_size']  = str(e)

    import_files = []
    import_urls  = []

    if 'import_urls' in input:
        for import_url in input['import_urls']:
            import_urls.append(import_url)

    if 'track_url' in input:
        import_urls.append(input['track_url'])
    if 'umap_url' in input:
        import_urls.append(input['umap_url'])

    for import_url in import_urls:
            try:
                import_file = _get_remote_file(import_url)
                import_files.append(import_file)
            except Exception as e:
                result['error']['import_url'] = "Can't fetch import_url: %s" % e

    for import_file in request.FILES:
        import_files.append(request.FILES[import_file])

    processed_files = []

    if len(import_files) > 0:
        import_data = {
            'lat_bottom_right' : 90,
            'lat_upper_left'   : -90,
            'lon_bottom_right' : 180,
            'lon_upper_left'   : -180,
            'maptitles'        : [],
            'layout'           : False,
        }

        for import_file in import_files:
            try:
                filetype = ocitysmap.guess_filetype(import_file)
                if filetype == 'gpx':
                    import_result = _process_gpx_file(import_file)
                elif filetype == 'poi':
                    import_result = _process_poi_file(import_file)
                elif filetype == 'umap':
                    import_result = _process_umap_file(import_file)
                else:
                    result['error']['import_file'] = "Can't determine import file type for %s" % import_file.name
                    break
            except Exception as e:
                result['error']['import_file'] = "Error processing import file: %s" % e
                break

            import_data['lat_bottom_right'] = min(import_data['lat_bottom_right'],
                                                  import_result['lat_bottom_right'])
            import_data['lat_upper_left']   = max(import_data['lat_upper_left'],
                                                  import_result['lat_upper_left'])
            import_data['lon_bottom_right'] = min(import_data['lon_bottom_right'],
                                                  import_result['lon_bottom_right'])
            import_data['lon_upper_left']   = max(import_data['lon_upper_left'],
                                                  import_result['lon_upper_left'])
            if 'maptitle' in import_result:
                import_data['maptitles'].append(import_result['maptitle'])

            if 'layout' in import_result:
                import_data['layout'] = import_result['layout']

            if 'file' in import_result:
                import_file = import_result['file']

            processed_files.append((import_result['type'], import_file))

        if not result['error']:
            if _no_geometry(job):
                job.lat_bottom_right = import_data['lat_bottom_right']
                job.lon_bottom_right = import_data['lon_bottom_right']
                job.lat_upper_left   = import_data['lat_upper_left']
                job.lon_upper_left   = import_data['lon_upper_left']

            if not job.maptitle:
                job.maptitle = ", ".join(import_data['maptitles'])

            if not job.layout:
                job.layout = import_data['layout']

    if _no_geometry(job):
        result['error']['geometry'] = 'No bounding box or OSM id given'

    if not job.layout:
        job.layout = 'plain'

    job.queue = 'api'

    if not result['error']:
        job.status = 0
        if www.settings.SUBMITTER_IP_LIFETIME != 0:
            job.submitterip = request.META['REMOTE_ADDR']
        else:
            job.submitterip = None

        job.index_queue_at_submission = (models.MapRenderingJob.objects.queue_size(job.queue))
        job.nonce = helpers.generate_nonce(models.MapRenderingJob.NONCE_SIZE)
        try:
            job.full_clean()
            job.save()

            if len(processed_files):
                for (file_type, file_entry) in processed_files:
                    file_instance =  models.UploadFile(uploaded_file = file_entry,
                                                       file_type     = file_type)
                    file_instance.save()
                    file_instance.job.add(job)

            reply = model_to_dict(job)

            result['id']              = reply['id']
            result['status']          = reply['status']
            result['status_msg']      = job_stati_dict(reply['status'])
            if reply['status'] == 0:
                result['queue_size'] = models.MapRenderingJob.objects.queue_size()
            else:
                result['queue_size'] = 0

            result['files'] = {}

            result['interactive']     = request.build_absolute_uri('../../maps/%d' % reply['id'])

            if reply['administrative_osmid']:
                result['osm_id']      = reply['administrative_osmid']
            else:
                result['bbox_top']    = reply['lat_upper_left']
                result['bbox_bottom'] = reply['lat_bottom_right']
                result['bbox_left']   = reply['lon_upper_left']
                result['bbox_right']  = reply['lon_bottom_right']

            result['title']           = reply['maptitle']
            result['layout']          = reply['layout']
            result['style']           = reply['stylesheet']
            if reply['overlay']:
                result['overlays']    = reply['overlay'].split(',')
            result['language']        = reply['map_language']
            result['paper_height_mm'] = reply['paper_height_mm']
            result['paper_width_mm']  = reply['paper_width_mm']
        except ValidationError as e:
            result['error'] = e.message_dict
        except Exception as e:
            result['error']['reason'] = str(e)

    if result['error']:
        status = 400
    else:
        del result['error']
        status = 202

    return HttpResponse( content=json.dumps(result, indent=4, sort_keys=True, default=str)
                         , content_type='text/json', status=status)



def _no_geometry(job):
    return not job.administrative_osmid and not job.lat_upper_left

def _geojson_get_bounds(coords, bounds = [180, -180, 90, -90]):
    if isinstance(coords[0], list):
        for coord in coords:
            bounds = _geojson_get_bounds(coord, bounds)
    else:
        bounds[0] = min(coords[0], bounds[0])
        bounds[1] = max(coords[0], bounds[1])
        bounds[2] = min(coords[1], bounds[2])
        bounds[3] = max(coords[1], bounds[3])

    return bounds

def _get_remote_file(url):
    r = requests.get(url)
    with NamedTemporaryFile(delete=False) as f:
        f.write(r.content)
        name = path.basename(url)
        if name == '':
            name = path.basename(f.name)
    file = File(open(f.name, "rb"), name)
    file.url = url
    return file

def _process_umap_file(file):
    result = {'type': 'umap'}

    try:
        # read umap file contents
        file.open()
        umapjson = file.read().decode('utf-8-sig')

        # parse JSON contents into python dict
        umap = json.loads(umapjson)

        # use umap name as map title
        if umap['properties']['name']:
            result['maptitle'] = umap['properties']['name']

        # make sure we have a 'layers' list, there is none if Umap /geojson
        # URL scheme was used ...
        if not 'layers' in umap:
            umap['layers'] = []

        # Umap /geojson URL exports do not contain the actual data layers,
        # they only list internal layer Id and name, and provide the
        # necessary URL pattern to fetch the layer details
        # so if a 'datalayers' list is found in the properties we need
        # to download actual layer JSON and merge it into the
        # 'layers' list
        if hasattr(file, 'url') and 'datalayers' in umap['properties']:
            # first create full layer download URL from datalayer_view information
            dataview_url_template = urllib.parse.urljoin(file.url,
                                                         umap['properties']['urls']['datalayer_view'])
            # now process all data layer references
            for datalayer in umap['properties']['datalayers']:
                # replace {pk} placeholder with actual internal layer id
                dataview_url = dataview_url_template.replace('{pk}', str(datalayer['id']))

                try:
                    # download and parse layer json file
                    layerfile = _get_remote_file(dataview_url)
                    layerjson = layerfile.read().decode('utf-8-sig')
                    layerdata = json.loads(layerjson)

                    # append downloaded layer details data to layers list
                    umap['layers'].append(layerdata)
                except Exception as e:
                    raise RuntimeError('Could not fetch umap data layer %s: %s' % (datalayer['name'], e))

        # if no map bounding box is specified yet:
        # process all layers and merge their feature bounding boxes
        # so that all umap layer features fit on the map
        bounds = [180, -180, 90, -90]
        for layer in umap['layers']:
            for feature in layer['features']:
                bounds = _geojson_get_bounds(feature['geometry']['coordinates'], bounds)

        # add an extra 5% on each side so that features will not be
        # placed directly on the map edge, also ensure a minimum
        # non-zero size to aviod div-by-zero problems later by making
        # the extra border at least about one arc second wide
        d_lon = max((bounds[1] - bounds[0]) * 0.05, 0.0003)
        d_lat = max((bounds[3] - bounds[2]) * 0.05, 0.0003)

        result['lat_bottom_right'] = bounds[2] - d_lat
        result['lat_upper_left']   = bounds[3] + d_lat
        result['lon_bottom_right'] = bounds[0] - d_lon
        result['lon_upper_left']   = bounds[1] + d_lon

        # save potentially modified umap JSON data
        result['file'] = ContentFile(json.dumps(umap, indent=4, sort_keys=True, default=str), name=file.name)

    except Exception as e:
        raise RuntimeError('Cannot process Umap file: %s %s' % (e, file.name))

    return result

def _process_gpx_file(file):
    result = {'type': 'gpx'}

    try:
        file.open()
        gpxxml = file.read().decode('utf-8-sig')
        gpx = gpxpy.parse(gpxxml)

        (min_lat, max_lat, min_lon, max_lon) = gpx.get_bounds()
        d_lat = (max_lat - min_lat) * 0.05
        d_lon = (max_lon - min_lon) * 0.05

        result['lat_bottom_right'] = min_lat - d_lat
        result['lat_upper_left']   = max_lat + d_lat
        result['lon_bottom_right'] = min_lon - d_lon
        result['lon_upper_left']   = max_lon + d_lon

        if gpx.name:
            result['maptitle'] = gpx.name

    except Exception as e:
        raise RuntimeError('Cannot parse GPX track: %s' % e)

    return result

def _process_poi_file(file):
    result = {'type': 'poi'}

    try:
        file.open()
        poijson = file.read().decode('utf-8-sig')

        poi = json.loads(poijson)

        if 'title' in poi:
            result['maptitle'] = poi['title']

        bounds = [180, -180, 90, -90]
        for cat in poi['nodes']:
            for node in cat['nodes']:
                bounds[0] = min(float(node['lon']), bounds[0])
                bounds[1] = max(float(node['lon']), bounds[1])
                bounds[2] = min(float(node['lat']), bounds[2])
                bounds[3] = max(float(node['lat']), bounds[3])

        d_lon = (bounds[1] - bounds[0]) * 0.05
        d_lat = (bounds[3] - bounds[2]) * 0.05

        result['lat_bottom_right'] = bounds[2] - d_lat
        result['lat_upper_left']   = bounds[3] + d_lat
        result['lon_bottom_right'] = bounds[0] - d_lon
        result['lon_upper_left']   = bounds[1] + d_lon

        result['layout'] = 'single_page_index_side'

    except Exception as e:
        raise RuntimeError('Cannot parse POI file: %s' % e)

    return result
