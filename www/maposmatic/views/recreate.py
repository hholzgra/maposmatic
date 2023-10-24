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

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse

import www.settings
from www.maposmatic import helpers, forms, models


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

            newjob.layout = job.layout
            newjob.indexer = job.indexer
            newjob.stylesheet = job.stylesheet
            newjob.overlay = job.overlay

            newjob.logo = job.logo
            newjob.extra_logo = job.extra_logo
            newjob.extra_text = job.extra_text

            newjob.queue = "default"
            if job.layout.startswith('multi'):
                newjob.queue = 'multipage'

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
                                                .queue_size() + 1)
            newjob.nonce = helpers.generate_nonce(models.MapRenderingJob.NONCE_SIZE)

            newjob.save()

            for each in job.uploads.all():
                each.job.add(newjob)

            return HttpResponseRedirect(reverse('map-by-id-and-nonce',
                                                args=[newjob.id, newjob.nonce]))

    return HttpResponseBadRequest("ERROR: Invalid request")

