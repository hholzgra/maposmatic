import www.settings

from .extratags import register

import os

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.html import escape

def _lastline(filename):
    try:
        with open(filename, "rb") as file:
            file.seek(-2, os.SEEK_END)
            while file.read(1) != b'\n':
                file.seek(-2, os.SEEK_CUR)
            return str(file.readline().decode())
    except:
        return ""

@register.filter()
def error_log_tail(value):
    error_log_tail = escape(_lastline(value.get_errorlog_file())).replace(':',':<br/>')
    return mark_safe(error_log_tail)

@register.filter()
def email_url(value):
    return mark_safe("<a href='mailto:%(email)s?subject=[MapOSMatic] Error on request %(id)d'><i class='fas fa-envelope'></i> %(email)s</a>" % {
        "email": www.settings.CONTACT_EMAIL,
        "id":    value.id
    })



