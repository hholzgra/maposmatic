#!/usr/bin/python3
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

import logging
import os
import sys
import threading
import time
from functools import reduce
import glob
from datetime import datetime

import django
django.setup()

from www.maposmatic.models import MapRenderingJob, UploadFile
from www.settings import RENDERING_RESULT_PATH, RENDERING_RESULT_MAX_SIZE_GB, RENDERING_RESULT_MAX_PURGE_ITERATIONS, MEDIA_ROOT

import render

from django import db

LOG = logging.getLogger('maposmatic')

_DEFAULT_POLL_FREQUENCY = 10        # Daemon job polling frequency, in seconds

_RESULT_MSGS = {
    render.RESULT_SUCCESS: 'ok',
    render.RESULT_KEYBOARD_INTERRUPT: 'Rendering interrupted',
    render.RESULT_PREPARATION_EXCEPTION: 'Data preparation failed',
    render.RESULT_RENDERING_EXCEPTION: 'Rendering failed',
    render.RESULT_TIMEOUT_REACHED: 'Rendering took too long, canceled',
    render.RESULT_MEMORY_EXCEEDED: 'Not enough memory to render, try a smaller region or a simpler stylesheet'
}

LOG = logging.getLogger('maposmatic')

class MapOSMaticDaemon:
    """
    This is a basic rendering daemon, base class for the different
    implementations of rendering scheduling. By default, it acts as a
    standalone, single-process MapOSMatic rendering daemon.

    It of course uses the TimingOutJobRenderer to ensure no long-lasting job
    stalls the queue.
    """

    def __init__(self, frequency=_DEFAULT_POLL_FREQUENCY, queue_name="default"):
        self.frequency = frequency
        self.queue_name = queue_name
        LOG.info("MapOSMatic rendering daemon started.")
        self.rollback_orphaned_jobs()

    def rollback_orphaned_jobs(self):
        """Reset all jobs left in the "rendering" state back to the "waiting"
        state to process them correctly."""
        MapRenderingJob.objects.filter(status=1).update(status=0)

    def serve(self):
        """Implement a basic service loop, looking every self.frequency seconds
        for a new job to render and dispatch it if one's available. This method
        can of course be overloaded by subclasses of MapOSMaticDaemon depending
        on their needs."""

        cleanup = RenderingsGarbageCollector()

        # check disk space once up front
        try:
            cleanup.cleanup()
        except Exception as e:
            LOG.warning("Cleanup failed: %s" % e)

        while True:
            try:
                job = MapRenderingJob.objects.to_render(self.queue_name)[0]
                self.dispatch(job)

                # check disk space after rendering 
                try:
                    cleanup.cleanup()
                except Exception as e:
                    LOG.warning("Cleanup failed: %s" % e)
            except IndexError: # no pending job found
                try:
                    time.sleep(self.frequency) # wait a bit before checking again
                except KeyboardInterrupt:
                    break

        LOG.info("MapOSMatic rendering daemon terminating.")

    def dispatch(self, job):
        """In this simple single-process daemon, dispatching is as easy as
        calling the render() method. Subclasses probably want to overload this
        method too and implement a more clever dispatching mechanism.

        Args:
            job (MapRenderingJob): the job to process and render.

        Returns True if the rendering was successful, False otherwise.
        """

        return self.render(job, 'maposmaticd_%d_' % os.getpid())

    def render(self, job, prefix=None):
        """Render a given job. Uses get_renderer() to get the appropriate
        renderer to use to render this job.

        Args:
            job (MapRenderingJob): the job to process and render.
            renderer (JobRenderer): the renderer to use.

        Returns True if the rendering was successful, False otherwise.
        """
        renderer = self.get_renderer(job, prefix)
        job.start_rendering()

        # make sure that existing DB connections are not re-used
        # by the forked subprocess ...
        db.connections.close_all()

        ret = renderer.run()
        job.end_rendering(_RESULT_MSGS[ret])
        return ret == 0

    def get_renderer(self, job, prefix):
        return render.ThreadingJobRenderer(job, prefix=prefix)

class ForkingMapOSMaticDaemon(MapOSMaticDaemon):

    def __init__(self, frequency=_DEFAULT_POLL_FREQUENCY, queue_name="default"):
        MapOSMaticDaemon.__init__(self, frequency, queue_name)
        LOG.info('This is the forking daemon. Will fork to process each job.')

    def get_renderer(self, job, prefix):
        return render.ForkingJobRenderer(job, prefix=prefix)

class RenderingsGarbageCollector:
    """
    A garbage collector thread that removes old rendering from
    RENDERING_RESULT_PATH when the total size of the directory goes about 80%
    of RENDERING_RESULT_MAX_SIZE_GB.
    """

    def get_file_info(self, path):
        """Returns a dictionary of information on the given file.

        Args:
            path (string): the full path to the file.
        Returns a dictionary containing:
            * name: the file base name;
            * path: its full path;
            * size: its size;
            * time: the last time the file contents were changed."""

        s = os.stat(path)
        return {'name': os.path.basename(path),
                'path': path,
                'size': s.st_size,
                'time': s.st_mtime}

    def get_formatted_value(self, value):
        """Returns the given value in bytes formatted for display, with its
        unit."""
        return '%.1f MiB' % (value/1024.0/1024.0)

    def get_formatted_details(self, saved, size, threshold):
        """Returns the given saved space, size and threshold details, formatted
        for display by get_formatted_value()."""

        return 'saved %s, now %s/%s (%d%%)' % \
                (self.get_formatted_value(saved),
                 self.get_formatted_value(size),
                 self.get_formatted_value(threshold),
                 size*100/threshold
                 )

    def cleanup(self):
        """Run one iteration of the cleanup loop. A sorted list of files from
        the renderings directory is first created, oldest files last. Files are
        then pop()-ed out of the list and removed by cleanup_files() until
        we're back below the size threshold."""

        files = list(map(lambda f: self.get_file_info(f),
                    [os.path.join(f)
                        for f in glob.iglob(os.path.join(RENDERING_RESULT_PATH, '**'), recursive=True)
                        if not (os.path.isdir(f) or
                                f.startswith('.') or
                                f.endswith(render.THUMBNAIL_SUFFIX))]))

        # Compute the total size occupied by the renderings, and the actual
        # threshold, in bytes.
        size = reduce(lambda x,y: x+y['size'], files, 0)
        threshold = RENDERING_RESULT_MAX_SIZE_GB * 1024 * 1024 * 1024

        LOG.info("Cleanup status: %.1f of %.1f GB used" % (size / (1024*1024*1024), threshold / (1024*1024*1024)))

        # Stop here if we are below the threshold
        if size < threshold:
            return

        LOG.info("%s consumed for a %s threshold. Cleaning..." %
                 (self.get_formatted_value(size),
                  self.get_formatted_value(threshold)))

        # Sort files by timestamp, oldest last, and start removing them by
        # pop()-ing the list.
        LOG.info("Cleanup sorting %d files" % len(files))
        files.sort(key = lambda file: file['time'], reverse = True)

        LOG.info("Cleanup processing file list")
        iterations = 0
        previous_job_id = 0
        while size > ( 0.9 * threshold):
            if iterations > RENDERING_RESULT_MAX_PURGE_ITERATIONS:
                LOG.info("%d delete iterations done, pausing until next invocation" % RENDERING_RESULT_MAX_PURGE_ITERATIONS)
                break
            if not len(files):
                LOG.error("No files to remove and still above threshold! "
                          "Something's wrong!")
                return

            f = files.pop()
            job = MapRenderingJob.objects.get_by_filename(f['path'])
            if job:
                if job.id != previous_job_id:
                    previous_job_id = job.id
                    removed, saved = job.remove_all_files()
                    size -= saved
                    if removed:
                        iterations += 1
                        LOG.info("Cleanup removed %d files for job #%d (%s)." %
                                 (removed, job.id,
                                  self.get_formatted_details(saved, size,
                                                             threshold)))

            else:
                # If we didn't find a parent job, it means this is an orphaned
                # file, we can safely remove it to get back some disk space.
                try:
                    os.remove(f['path'])
                    size -= f['size']
                    LOG.info("Cleanup: Removed orphan file %s (%s)." %
                             (f['name'], self.get_formatted_details(f['size'],
                                                                    size,
                                                                    threshold)))
                except:
                    pass



    LOG.info("Cleanup remove old upload files")
    files = UploadFile.objects.filter(keep_until__lte = datetime.now())

    for file in files:
        try:
            os.remove(os.path.join(MEDIA_ROOT, file.uploaded_file.name))
            LOG.info("Cleanup: removed %s" % file.upload_file.name)
        except:
            pass

if __name__ == '__main__':
    if (not os.path.exists(RENDERING_RESULT_PATH)
        or not os.path.isdir(RENDERING_RESULT_PATH)):
        LOG.error("%s does not exist or is not a directory! " %
                  RENDERING_RESULT_PATH)
        LOG.error("Please set RENDERING_RESULT_PATH to a valid directory!")
        sys.exit(1)

    try:
        if len(sys.argv) == 2:
            daemon = ForkingMapOSMaticDaemon(queue_name=sys.argv[1])
        else:
            daemon = ForkingMapOSMaticDaemon()
        daemon.serve()
    except Exception as e:
        LOG.exception('Fatal error during daemon execution!')

