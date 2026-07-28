#!/usr/bin/env python3
# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2009  David Decotigny
# Copyright (C) 2009  Frédéric Lehobey
# Copyright (C) 2009  David Mentré
# Copyright (C) 2009  Maxime Petazzoni
# Copyright (C) 2009  Thomas Petazzoni
# Copyright (C) 2009  Gaël Utard

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
import sys

from config import OCITYSMAP_PATH, MAPOSMATIC_LOG, MAPOSMATIC_LVL

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, '..'))

    os.environ['PYTHONPATH'] = '%s:%s:%s' % (OCITYSMAP_PATH, root,
                                             os.environ.get('PYTHONPATH', ''))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'www.settings'
    os.environ['MAPOSMATIC_LOG_FILE'] = MAPOSMATIC_LOG or ''
    os.environ['MAPOSMATIC_LOG_LEVEL'] = str(MAPOSMATIC_LVL)

    os.execv(os.path.join(root, sys.argv[1]), sys.argv[1:])
