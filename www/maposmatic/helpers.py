# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2009  David Decotigny
# Copyright (C) 2009  Frédéric Lehobey
# Copyright (C) 2009  Pierre Mauduit
# Copyright (C) 2009  David Mentré
# Copyright (C) 2009  Maxime Petazzoni
# Copyright (C) 2009  Thomas Petazzoni
# Copyright (C) 2009  Gaël Utard
# Copyright (C) 2017  Hartmut Holzgraefe

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
import psycopg2
import random
import string
import secrets

from www.maposmatic.models import MapRenderingJob
import www.settings

def get_pages_list(page, paginator):
    """Returns a list of number.
    It contains the id of the pages to display for a page given."""

    # Navigation pages
    nav = {}
    page_list = []
    last = False

    for i in [1, 2,
              page.number-1, page.number, page.number+1,
              paginator.num_pages-1, paginator.num_pages]:
        nav[i] = True

    for i in range(1, paginator.num_pages+1):
        if i in nav:
            if last and i - last > 1:
                page_list.append('...')
            page_list.append(i)
            last = i
    return page_list

def generate_nonce(length):
    return ''.join(secure.token_hex(length//2) for i in range(length))
