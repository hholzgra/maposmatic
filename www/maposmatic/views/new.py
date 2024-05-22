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

import datetime
from ipware import get_client_ip

from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponseRedirect, HttpResponseNotAllowed
from django.shortcuts import render
from django.utils.translation import gettext, gettext_lazy as _
from django.utils.safestring import mark_safe
from django.urls import reverse

import www.settings
from www.maposmatic import helpers, forms, models, views

import ocitysmap

def _create_upload_file(job, file, keep_until = None):
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

def _new_POST(request):
    form = forms.MapRenderingJobForm(request.POST, request.FILES)

    if not form.is_valid():
        data = {'form': form }
        return render(request, 'generic_error.html', data)

    # remember some settings as future defaults
    request.session['new_layout']          = form.cleaned_data.get('layout')
    request.session['new_indexer']         = form.cleaned_data.get('indexer')
    request.session['new_stylesheet']      = form.cleaned_data.get('stylesheet')
    request.session['new_overlay']         = form.cleaned_data.get('overlay')
    request.session['new_paper_width_mm']  = form.cleaned_data.get('paper_width_mm')
    request.session['new_paper_height_mm'] = form.cleaned_data.get('paper_height_mm')

    job = form.save(commit=False)
    job.administrative_osmid = form.cleaned_data.get('administrative_osmid')
    job.stylesheet = form.cleaned_data.get('stylesheet')
    job.overlay = ",".join(form.cleaned_data.get('overlay'))
    job.layout = form.cleaned_data.get('layout')
    if job.layout.startswith('multi'):
        job.queue = 'multipage'
    job.indexer = form.cleaned_data.get('indexer')
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
                                     .queue_size(job.queue) + 1)
    job.nonce = helpers.generate_nonce(models.MapRenderingJob.NONCE_SIZE)

    client_ip, is_routable = get_client_ip(request)
    if www.settings.EXTRA_IP is None or ( client_ip is not None and client_ip.startswith(www.settings.EXTRA_IP )):
        # TODO make this behave more like MAINTENANCE_MODE_IGNORE_IP_ADDRESSES
        # comparing to a list of addresses properly instead of just doing simple
        # partial string comparison
        job.extra_text = www.settings.EXTRA_FOOTER
        job.logo = "bundled:osm-logo.svg"
        job.extra_logo = www.settings.EXTRA_LOGO
        job.queue = "api"

    job.save()

    files = request.FILES.getlist('uploadfile')
    if form.cleaned_data.get('delete_files_after_rendering'):
        keep_until = None
    else:
        if www.settings.UPLOAD_FILE_LIFETIME > 0:
            keep_until = datetime.datetime.now() + datetime.timedelta(days=www.settings.UPLOAD_FILE_LIFETIME)
        else:
            keep_until = '2999-12-30' # arbitrary 'max' value
    for file in files:
        _create_upload_file(job, file, keep_until)

    return HttpResponseRedirect(reverse('map-by-id-and-nonce',
                                        args=[job.id, job.nonce]))


def _new_GET(request):
    init_vals = request.GET.dict()
    oc = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)

    if not 'layout' in init_vals and 'new_layout' in request.session :
        init_vals['layout'] = request.session['new_layout']
    else:
        request.session['new_layout'] = oc.get_all_renderer_names()[0]

    if not 'indexer' in init_vals and 'new_indexer' in request.session :
        init_vals['indexer'] = request.session['new_indexer']
    else:
        request.session['new_indexer'] = 'Street' # TODO make configurable

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

    papersize_buttons, multisize_buttons = views._papersize_buttons()

    return render(request, 'maposmatic/new.html',
                  { 'form' :                           form ,
                    'papersize_suggestions':           mark_safe(papersize_buttons),
                    'multipage_papersize_suggestions': mark_safe(multisize_buttons),
                   })

def new(request):
    """The map creation page and form."""
    if request.method == 'POST':
        return _new_POST(request)
    elif request.method == 'GET':
        return _new_GET(request)
    else:
        return HttpResponseNotAllowed(request.method)
