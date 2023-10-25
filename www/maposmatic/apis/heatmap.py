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
from django.db import connections

import ocitysmap

import www.settings
from www.maposmatic import helpers, forms, models


def heatdata(request, days=1):
    query = """
select round(lat::numeric, 4)::float as lat
     , round(lng::numeric, 4)::float as lng
     , count(*) as count
  from (   
select (lat_upper_left + lat_bottom_right)/2 as lat
     , (lon_upper_left + lon_bottom_right)/2 as lng
  from maposmatic_maprenderingjob
 where lat_upper_left is not null
   and submission_time BETWEEN LOCALTIMESTAMP - INTERVAL '%s days' AND LOCALTIMESTAMP

union

select (north + south)/2 as lat
     , (west + east)/2 as lng
  from maposmatic_maprenderingjob m
  left outer join dblink('dbname=gis', 'SELECT osm_id, west, east, north, south FROM place') AS p(osm_id bigint, west float, east float, north float, south float)
  on -m.administrative_osmid = p.osm_id
  where m.administrative_osmid is not null
   and submission_time BETWEEN LOCALTIMESTAMP - INTERVAL '%s days' AND LOCALTIMESTAMP

) x group by lat, lng;
;
""" % (days, days)

    data = { "max": 8, "data": [] }
    
    try:
        cursor = connections['default'].cursor()
        if cursor is None:
            raise Http404("postgis: no cursor")

        cursor.execute(query)

        columns = [col[0] for col in cursor.description]

        for row in cursor.fetchall():
            data["data"].append(dict(zip(columns, row)))

        cursor.close()

        return HttpResponse(content="var data = " + json.dumps(data, indent=2),
                            content_type='application/javascript')

    except Exception as e:
        raise RuntimeError(e)

    

