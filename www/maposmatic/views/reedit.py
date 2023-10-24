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
from www.maposmatic.apis import get_paper_from_size


def reedit(request):
    if request.method == 'POST':
        form = forms.MapRecreateForm(request.POST)
        if form.is_valid():
            job = get_object_or_404(models.MapRenderingJob,
                                    id=form.cleaned_data['id'])

        paper_size, paper_orientation = get_paper_from_size(job.paper_width_mm, job.paper_height_mm)

        init_vals = {
            'layout':           job.layout,
            'indexer':          job.indexer,
            'stylesheet':       job.stylesheet,
            'overlay':          job.overlay.split(","),
            'maptitle':         job.maptitle,
            'submittermail':    job.submittermail,
            'default_papersize':        paper_size,
            'default_paperorientation': paper_orientation,
        }

        request.session['new_layout']     = job.layout
        request.session['new_indexer']    = job.indexer
        request.session['new_stylesheet'] = job.stylesheet
        request.session['new_overlay']    = job.overlay.split(",")

        form = forms.MapRenderingJobForm(initial=init_vals)

        bounds = "L.latLngBounds(L.latLng(%f,%f),L.latLng(%f,%f))" % (job.lat_upper_left,
                                                                      job.lon_upper_left,
                                                                      job.lat_bottom_right,
                                                                      job.lon_bottom_right)

        return render(request,
                      'maposmatic/new.html',
                      {
                          'form' : form,
                          'SELECTION_BOUNDS': bounds,
                      })

    return HttpResponseBadRequest("ERROR: Invalid request")

