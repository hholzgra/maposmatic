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

import json

from django.http import HttpResponse

import www.settings
from www.maposmatic import nominatim

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





