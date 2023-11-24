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

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _
from django.utils.safestring import mark_safe


from www.maposmatic import helpers, forms, models, views

def reedit(request):
    if request.method == 'POST':
        form = forms.MapRecreateForm(request.POST)
        if form.is_valid():
            job = get_object_or_404(models.MapRenderingJob,
                                    id=form.cleaned_data['id'])


        init_vals = {
            'layout':           job.layout,
            'indexer':          job.indexer,
            'stylesheet':       job.stylesheet,
            'overlay':          job.overlay.split(","),
            'maptitle':         job.maptitle,
            'submittermail':    job.submittermail,
            'paper_width_mm':   job.paper_width_mm,
            'paper_height_mm':  job.paper_height_mm,
        }

        form = forms.MapRenderingJobForm(initial=init_vals)

        papersize_buttons, multisize_buttons = views._papersize_buttons()
        
        bounds = "L.latLngBounds(L.latLng(%f,%f),L.latLng(%f,%f))" % (job.lat_upper_left,
                                                                      job.lon_upper_left,
                                                                      job.lat_bottom_right,
                                                                      job.lon_bottom_right)

        return render(request,
                      'maposmatic/new.html',
                      {
                          'form' : form,
                          'papersize_suggestions':           mark_safe(papersize_buttons),
                          'multipage_papersize_suggestions': mark_safe(multisize_buttons),
                          'SELECTION_BOUNDS': bounds,
                      })

    return HttpResponseBadRequest("ERROR: Invalid request")

