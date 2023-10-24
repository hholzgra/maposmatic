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

from django.shortcuts import render
from www.maposmatic import helpers, forms, models

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
