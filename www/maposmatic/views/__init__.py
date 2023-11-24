# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2023  Hartmut Holzgraefe

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

import www.settings

import ocitysmap

from django.utils.translation import gettext, gettext_lazy as _

# helper for the "new" and "reedit" views
def _papersize_button(basename, width=None, height=None):
    format = "<button id='{0}_{1}_{2}' type='button' class='btn btn-primary papersize papersize_{1}_{2}' onclick='set_papersize({1}, {2});'><i class='fas fa-{3} fa-2x'></i></button> "

    if width is None or height is None: # no values -> "best fit"
        return format.format(basename, "best", "fit", 'square')

    if width == height: # square format, just one button
        return format.format(basename, width, height, 'square')

    # individual buttons for landscape and portrait
    return format.format(basename, height, width, 'image') + format.format(basename, width, height, 'portrait')

def _papersize_buttons():
    _ocitysmap = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)

    papersize_buttons = '<p>'
    papersize_buttons += _papersize_button('paper')
    papersize_buttons += "<b>%s</b> (<span id='best_width'>?</span>&times;<span id='best_height'>?</span>mm²)</p>" % _("Best fit")
    for p in _ocitysmap.get_all_paper_sizes():
        if p[1] is not None:
            papersize_buttons += "<p>"
            papersize_buttons += _papersize_button('paper', p[1], p[2])
            papersize_buttons += "<b>%s</b> (%s&times;%smm²)</p>" % (p[0], repr(p[1]), repr(p[2]))

    multisize_buttons = ''
    for p in _ocitysmap.get_all_paper_sizes('multipage'):
        if p[1] is not None:
            multisize_buttons += "<p>"
            multisize_buttons += _papersize_button('multipaper', p[1], p[2])
            multisize_buttons += "<b>%s</b> (%s&times;%smm²)</p>" % (p[0], repr(p[1]), repr(p[2]))

    return papersize_buttons, multisize_buttons

from .index         import index

from .about         import about
from .privacy       import privacy
from .documentation import documentation_user_guide, documentation_api
from .donate        import donate, donate_thanks

from .maps          import maps
from .map_full      import map_full
from .new           import new
from .recreate      import recreate
from .reedit        import reedit
from .cancel        import cancel

from .heatmap       import heatmap

from .congo         import congo


