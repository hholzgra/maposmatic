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

from django.http import HttpResponse

import ocitysmap

import www.settings

def paper_formats(request):
    _ocitysmap = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)
    
    result = {}
    for p in _ocitysmap.get_all_paper_sizes():
        if p[1] and p[2]:
            result[p[0]] = {'width': p[1], 'height': p[2]}

    return HttpResponse( content=json.dumps(result,
                                            indent    = 4,
                                            sort_keys = True,
                                            default   = str),
                         content_type='text/json')
