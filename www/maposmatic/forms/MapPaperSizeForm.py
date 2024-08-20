# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2024  Hartmut Holzgraefe

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

from django import forms

class MapPaperSizeForm(forms.Form):
    """
    The map paper size form, which is only used to analyze the
    arguments of the POST request to /apis/papersize/
    """
    osmid            = forms.IntegerField(required=False)
    layout           = forms.CharField(max_length=256)
    indexer          = forms.CharField(max_length=256)
    stylesheet       = forms.CharField(max_length=256)
    lat_upper_left   = forms.FloatField(required=False, min_value=-90.0, max_value=90.0)
    lon_upper_left   = forms.FloatField(required=False, min_value=-180.0, max_value=180.0)
    lat_bottom_right = forms.FloatField(required=False, min_value=-90.0, max_value=90.0)
    lon_bottom_right = forms.FloatField(required=False, min_value=-180.0, max_value=180.0)
