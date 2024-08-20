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

class MapRecreateForm(forms.Form):
    """
    The map recreate form, to reschedule an already processed job on the queue.
    """

    id = forms.IntegerField(widget=forms.HiddenInput, required=True)

    def clean(self):
        data = self.cleaned_data

        try:
            data["id"] = int(data.get("id", 0))
        except ValueError:
            data["id"] = 0

        return data
