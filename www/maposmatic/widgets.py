#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009  Étienne Loks  <etienne.loks_AT_peacefrogsDOTnet>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# See the file COPYING for details.

"""
Extra widgets and fields
"""

from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from www import settings

class AreaWidget(forms.TextInput):
    """
    Manage the edition of an area on the map
    """
    def render(self, name, value, attrs=None, renderer=None):
        """
        Render the bbox selection widget.
        """
        # Initially the widget shows no bounding box and shows an area that
        # contains the France
        if value:
            upper_left_lat, upper_left_lon, \
                lower_right_lat, lower_right_lon = value
        else:
            upper_left_lat, upper_left_lon, \
                lower_right_lat, lower_right_lon = settings.BASE_BOUNDING_BOX

        alert = '<i class="fa fa-exclamation-triangle"></i>&nbsp;&nbsp;%s' % _('Area too big to be rendered!')

        tpl = u"""<div id="step-location-map"></div>
        <div class="row-fluid step-location-map-bbox">
          <div class="span12">
            <input type="hidden" name="lat_upper_left" id="id_lat_upper_left"
                   value="%(tl_lat)s" title="%(tl_lat_help)s" />
            <span id='lat_upper_left_info' class="well well-sm"></span>
            <input type="hidden" name="lon_upper_left" id="id_lon_upper_left"
                   value="%(tl_lon)s" title="%(tl_lon_help)s" />
            <span id='lon_upper_left_info' class="well well-sm"></span>
            &nbsp;&#8600;&nbsp;
            <input type="hidden" name="lat_bottom_right" id="id_lat_bottom_right"
                   value="%(br_lat)s" title="%(br_lat_help)s" />
            <span id='lat_bottom_right_info' class="well well-sm"></span>
            <input type="hidden" name="lon_bottom_right" id="id_lon_bottom_right"
                   value="%(br_lon)s" title="%(br_lon_help)s" />
            <span id='lon_bottom_right_info' class="well well-sm"></span>
            &nbsp;&nbsp;
            <span id='metric_info'></span>
          </div>
        </div>
        <div id="area-size-alert" class="alert alert-danger">%(alert)s</div>
        """ % {'tl_lat': upper_left_lat, 'tl_lon': upper_left_lon,
                   'br_lat': lower_right_lat, 'br_lon': lower_right_lon,
                   'tl_lat_help': _('Latitude of the top left corner'),
                   'tl_lon_help': _('Longitude of the top left corner'),
                   'br_lat_help': _('Latitude of the bottom right corner'),
                   'br_lon_help': _('Longitude of the bottom right corner'),
                   'alert': alert,
                   'clear': _('Remove any selected region from the map')
                  }

        return mark_safe(tpl)

    def value_from_datadict(self, data, files, name):
        """
        Return the appropriate values
        """
        return (data['lat_upper_left'], data['lon_upper_left'],
                 data['lat_bottom_right'], data['lon_bottom_right'])

class AreaField(forms.MultiValueField):
    '''
    Set the widget for the form field
    '''
    widget = AreaWidget

    def clean(self, value):
        pass

    def compress(self, data_list):
        if not data_list:
            return None
        return data_list

