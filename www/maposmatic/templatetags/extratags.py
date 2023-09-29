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

import os
import re

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.html import escape

import www.settings

import ocitysmap

register = template.Library()

from . import file_tags, geo_tags, l18n_tags, bbox_tags
from . import paper_tags, rss_feed_tags, job_tags


@register.filter()
def add_blank_after_comma(value):
    return value.replace(",",", ")

@register.filter('startswith')
def startswith(text, starts):
    return text.startswith(starts)

register.filter('abs', lambda x: abs(x))
register.filter('getitem', lambda d,i: d.get(i,''))
