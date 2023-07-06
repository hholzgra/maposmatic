import www.settings

from .extratags import register

import ocitysmap

@register.filter()
def paper_size(value):
    w = value.paper_width_mm
    h = value.paper_height_mm

    oc = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)
    size_name = oc.get_paper_size_name_by_size(w, h)

    if size_name is None:
        return "%d×%d mm²" % (w,h)
    else:
        return "%s (%d×%d mm²)" % (size_name, w, h)
