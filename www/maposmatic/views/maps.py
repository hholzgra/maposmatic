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

from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

import www.settings
from www.maposmatic import helpers, forms, models

def maps(request, category=None, extra=None):
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
        elif category == 'queue' and extra is not None:
            map_list = map_list.filter(queue=extra)

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
                              { 'maps':      maps,
                                'form':      form,
                                'category':  category,
                                'extra':     extra,
                                'is_search': form.is_valid(),
                                'pages':     helpers.get_pages_list(maps, paginator),
                               })

