# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2009  David Decotigny
# Copyright (C) 2009  Frédéric Lehobey
# Copyright (C) 2009  David Mentré
# Copyright (C) 2009  Maxime Petazzoni
# Copyright (C) 2009  Thomas Petazzoni
# Copyright (C) 2009  Gaël Utard
# Copyright (C) 2018  Hartmut Holzgraefe

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

import datetime
import os
import re

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

import www.settings

import ocitysmap

register = template.Library()

_alert_ok   = "<div class='alert alert-success' role='alert'>"
_alert_info = "<div class='alert alert-info'    role='alert'>"
_alert_warn = "<div class='alert alert-warning' role='alert'>"
_alert_err  = "<div class='alert alert-danger'  role='alert'>"
_alert_end  = "</div>"

@register.filter()
def job_status_to_str(value, arg="Rendering failed", autoescape=True):
    if value == 0:
        return mark_safe(_alert_info + str(_("Waiting for rendering to begin...")) + _alert_end)
    elif value == 1:
        return mark_safe(_alert_info + str(_("The rendering is in progress...")) + _alert_end)
    elif value == 2:
        if arg == 'ok':
            return mark_safe(_alert_ok + str(_("Rendering was successful.")) + _alert_end)
        else:
            if www.settings.CONTACT_EMAIL:
                return mark_safe(_alert_err + str(_("%(arg)s!<br/>Please check the error log or contact %(email)s for more information." % {'arg': arg, 'email': www.settings.CONTACT_EMAIL})) + _alert_end)
            else:
                return mark_safe( _alert_err + _str(_("%(arg)s! Please check the error log for more information.") % {'arg': arg}) + _alert_end)
    elif value == 3:
        if arg == 'ok':
            return mark_safe(_alert_info + str(_("Rendering is obsolete: the rendering was successful, but the files are no longer available.")) + _alert_end)
        else:
            return mark_safe(_alert_warn + str(_("Obsolete failed rendering: the rendering failed, and the incomplete files have been removed.")) + _alert_end)
    elif value == 4:
        return mark_safe(_alert_warn + str(_("The rendering was cancelled by the user.")) + _alert_end)

    return ''

def feedparsed(value):
    return datetime.datetime(*value[:6])

def file_basename(value):
    try:
      return os.path.basename(value.name)
    except:
      return ""

def add_blank_after_comma(value):
    return value.replace(",",", ")

def _dd2dms(value):
    abs_value = abs(value)
    degrees  = int(abs_value)
    frac     = abs_value - degrees
    minutes  = int(frac * 60)
    seconds  = (frac * 3600) % 60

    return (degrees, minutes, seconds)

def latitude(value):
    latitude = float(value)
    (degrees, minutes, seconds) = _dd2dms(latitude)
    hemisphere = 'N' if latitude >= 0 else 'S'

    return "%d°%d'%d\"%s" % (degrees, minutes, seconds, hemisphere)

def longitude(value):
    latitude = float(value)
    (degrees, minutes, seconds) = _dd2dms(latitude)
    hemisphere = 'E' if latitude >= 0 else 'W'

    return "%d°%d'%d\"%s" % (degrees, minutes, seconds, hemisphere)

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

def language_flag(value):
    if value in www.settings.LANGUAGE_FLAGS:
        if www.settings.LANGUAGE_FLAGS[value] != None:
            return ("flag-icon flag-icon-%s" % www.settings.LANGUAGE_FLAGS[value])
    return "fa fa-flag"

def locale_base(value):
    return re.sub('\..*', '', value)

def paper_size(value):
    w = value.paper_width_mm
    h = value.paper_height_mm

    oc = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)
    size_name = oc.get_paper_size_name_by_size(w, h)

    if size_name is None:
        return "%d×%d mm²" % (w,h)
    else:
        return "%s (%d×%d mm²)" % (size_name, w, h)

register.filter('feedparsed', feedparsed)
register.filter('abs', lambda x: abs(x))
register.filter('getitem', lambda d,i: d.get(i,''))
register.filter('file_basename', file_basename)
register.filter('add_blank_after_comma', add_blank_after_comma)
register.filter('latitude', latitude)
register.filter('longitude', longitude)
register.filter('bbox_km', bbox_km)
register.filter('language_flag', language_flag)
register.filter('locale_base', locale_base)
register.filter('paper_size', paper_size)
