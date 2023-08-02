import www.settings

from .extratags import register

def _dd2dms(value):
    abs_value = abs(value)
    degrees  = int(abs_value)
    frac     = abs_value - degrees
    minutes  = int(frac * 60)
    seconds  = (frac * 3600) % 60

    return (degrees, minutes, seconds)

@register.filter()
def latitude(value):
    latitude = float(value)
    (degrees, minutes, seconds) = _dd2dms(latitude)
    hemisphere = 'N' if latitude >= 0 else 'S'

    return "%d°%d'%d\"%s" % (degrees, minutes, seconds, hemisphere)

@register.filter()
def longitude(value):
    latitude = float(value)
    (degrees, minutes, seconds) = _dd2dms(latitude)
    hemisphere = 'E' if latitude >= 0 else 'W'

    return "%d°%d'%d\"%s" % (degrees, minutes, seconds, hemisphere)

