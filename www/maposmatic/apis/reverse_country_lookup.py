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

from django.http import HttpResponse, Http404
from django.db import connections

def api_postgis_reverse(request, lat, lon):
    lat = float(lat)
    lon = float(lon)
    cursor = None
    query = """select country_code
                 from country_osm_grid
                where st_contains(geometry,
                                  st_geomfromtext('POINT(%f %f)', 4326))
            """ % (lon, lat)

    LOG.debug("Reverse Lookup Query %s" % query)

    try:
        connections['osm'].rollback() # make sure there's no pending transaction
        cursor = connections['osm'].cursor()

        cursor.execute(query)
        country_code = cursor.fetchone()
        cursor.close()
        if country_code is None or len(country_code) < 1:
            raise Http404("postgis: country not found")

        return HttpResponse('{"address": {"country_code": "%s"}}' % country_code[0], content_type='text/json')
    except Exception as e:
        LOG.warning("reverse geo lookup failed: %s" % e)
        pass
    finally:
        # Close the DB cursor if necessary
        if cursor is not None and not cursor.closed:
            cursor.close()

    raise Http404("postgis: something went wrong")
