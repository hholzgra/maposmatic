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
from django.shortcuts import get_object_or_404, render

import ocitysmap

import www.settings
from www.maposmatic import helpers, forms, nominatim, models


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
