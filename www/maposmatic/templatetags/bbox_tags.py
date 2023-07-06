import www.settings

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


