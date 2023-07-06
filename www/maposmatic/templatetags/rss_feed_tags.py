import www.settings

from .extratags import register

import datetime

@register.filter()
def feedparsed(value):
    return datetime.datetime(*value[:6])

