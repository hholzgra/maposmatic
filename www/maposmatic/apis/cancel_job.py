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

from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict

import ocitysmap

import www.settings
from www.maposmatic import helpers, forms, models


def cancel_job(request):
    """API handler for canceling rendering requests"""

    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    if request.content_type == 'application/json':
        input = json.loads(request.body.decode('utf-8-sig'))
    else:
        input = json.loads(request.POST['job'])

    if not "id" in input or not "nonce" in input:
        return HttpResponseBadRequest()

    job = get_object_or_404(models.MapRenderingJob, id = input['id'])

    reply = model_to_dict(job)

    if input['nonce'] != reply['nonce']:
        return HttpResponseForbidden()

    if job.is_waiting():
        job.cancel()

    return HttpResponse(status=204)

