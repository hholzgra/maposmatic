#!/usr/bin/env python
# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2010  David Decotigny
# Copyright (C) 2010  Frédéric Lehobey
# Copyright (C) 2010  David Mentré
# Copyright (C) 2010  Maxime Petazzoni
# Copyright (C) 2010  Thomas Petazzoni
# Copyright (C) 2010  Gaël Utard

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

import sys

from django import db
from www.maposmatic.models import MapRenderingJob
from www.settings import RENDERING_RESULT_PATH, RENDERING_RESULT_FORMATS

class DbckHandler:
    pass

class DummyDbckHandler(DbckHandler):
    """
    A dummy MapOSMatic Dbck handler for the dry runs.  It does nothing but
    returning a detail message about the job status relevant to each check
    operation.
    """

    def do_obsolete(self, job):
        return 'elligible for obsolete status!'

    def do_admin_bbox(self, job):
        return 'has both admin and bbox values!'

    def do_locale(self, job):
        return 'no locale information!'

class RealDbckHandler(DummyDbckHandler):
    """
    The 'real' MapOSMatic Dbck handler that actually fixes jobs.  See each
    check operation details for more information and what's done in each case.
    """

    DEFAULT_LOCALE = 'en_US.UTF-8'

    def do_obsolete(self, job):
        """If the job is obsolete, but not marked as such in the database (i.e.
        its status is 2 'Done', but it doesn't have all its output files
        present), ask the job to remove all its files and mark itself as
        obsolete."""
        removed, saved = job.remove_all_files()
        return 'removed %d file(s) and marked obsolete.' % removed

    def do_admin_bbox(self, job):
        """If the job has both administrative boundary/osmID information and a
        bounding box, always prefer the OSM ID, and purge the bounding box
        information.  In the daemon, the OSM ID always takes precedence
        anyways."""
        job.lat_upper_left = None
        job.lon_upper_left = None
        job.lat_bottom_right = None
        job.lon_bottom_right = None
        job.save()
        return 'cleared bounding box, keeping osmid %d.' % \
            job.administrative_osmid

    def do_locale(self, job):
        """If the job has no locale defined, make sure it has one, using the
        DEFAULT_LOCALE defined in RealDbckHandler."""
        job.map_language = self.DEFAULT_LOCALE
        job.save()
        return 'missed locale information, fell back to %s.' % \
            self.DEFAULT_LOCALE

class MapOSMaticDbck:
    """
    A database checker/fixer for MapOSMatic.  It runs a series of checks on
    all jobs from the database, eventually taking action to fix things that are
    wrong if a capable DbckHandler is provided.

    To add checks, write a check function that makes use of the correction
    operation from a handler and add it to the list of checks.
    """

    def __init__(self, handler=None):
        self.jobs = MapRenderingJob.objects.all().order_by('id')
        self.handler = handler or DbckHandler()

        self.checks = [self.__check_obsolete,
                       self.__check_admin_bbox,
                       self.__check_locale,
                      ]

        print 'Starting MapOSMatic database checker: %d job(s), ' \
              '%d check(s) with %s.' % (self.jobs.count(), len(self.checks),
                                        self.handler.__class__.__name__)

    def run(self):
        for job in self.jobs:
            messages = []
            for check in self.checks:
                try:
                    messages.append(check(job))
                except (NotImplementedError, AttributeError):
                    messages.append("%s not available!" % check.__name__)

            messages = filter(None, messages)
            if len(messages):
                print ' + checking job #%d (%s): ' % (job.id, job.maptitle)
                for m in messages:
                    print '  `', m

        print 'Check/repair complete. Database queries performed: %d.' % \
            len(db.connection.queries)

    def __check_obsolete(self, job):
        """Checks the obsolete status of the given job.  If the job is in the
        done state (status=2) and does not have all its output files, it's
        obselete and should be cleaned."""
        if not job.is_done_ok():
            return

        files = job.output_files()
        if (len(files['maps']) < len(RENDERING_RESULT_FORMATS)-1 or
            (len(files['indeces']) > 0 and
             len(files['indeces']) < len(RENDERING_RESULT_FORMATS))):
            return self.handler.do_obsolete(job)

    def __check_admin_bbox(self, job):
        """Make sure we don't have mutually exclusive admin/bbox data."""
        if job.administrative_osmid and (job.lat_upper_left or
                                         job.lon_upper_left or
                                         job.lat_bottom_right or
                                         job.lon_bottom_right):
            return self.handler.do_admin_bbox(job)

    def __check_locale(self, job):
        """Make sure the job declares a map language."""
        if not job.map_language:
            return self.handler.do_locale(job)


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == '--dry-run':
        handler = DummyDbckHandler()
    else:
        handler = RealDbckHandler()

    MapOSMaticDbck(handler).run()
