import www.settings

from .extratags import register

import re

@register.filter()
def language_flag(value):
    if value in www.settings.LANGUAGE_FLAGS:
        if www.settings.LANGUAGE_FLAGS[value] != None:
            return ("fi fi-%s" % www.settings.LANGUAGE_FLAGS[value])
    return "fa fa-flag"

@register.filter()
def locale_base(value):
    return re.sub('\..*', '', value)
