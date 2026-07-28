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

from .extratags import register

import ocitysmap

@register.filter()
def bbox_km(value):
    boundingbox = ocitysmap.coords.BoundingBox(
        value.lat_upper_left,
        value.lon_upper_left,
        value.lat_bottom_right,
        value.lon_bottom_right)

    (height, width) = boundingbox.spheric_sizes()

    if width >= 1000 and height >= 1000:
        return "ca. %d x %d km²" % (width/1000, height/1000)

    return "ca. %d x %d m²" % (width, height)
