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

from django.urls import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from datetime import datetime, timedelta
import www.settings
import re
import os
from slugify import slugify

import logging
LOG = logging.getLogger('maposmatic')

def get_track_path(instance, filename):
    return ""

def get_umap_path(instance, filename):
    return ""

def get_poi_file_path(instance, filename):
    return ""

class MapRenderingJobManager(models.Manager):
    def to_render(self):
        return MapRenderingJob.objects.filter(status=0).order_by('submission_time')

    def queue_size(self):
        return MapRenderingJob.objects.filter(status=0).count()

    # We try to find a rendered map from the last 15 days, which still
    # has its thumbnail present.
    def get_random_with_thumbnail(self):
        fifteen_days_before = datetime.now() - timedelta(15)
        maps = (MapRenderingJob.objects.filter(status=2)
            .filter(submission_time__gte=fifteen_days_before)
            .filter(resultmsg='ok')
            .order_by('?')[0:10])
        for m in maps:
            if m.get_thumbnail():
                return m
        return None

    def get_by_filename(self, name):
        """Tries to find the parent MapRenderingJob of a given file from its
        filename. Both the job ID found in the first part of the prefix and the
        entire files_prefix is used to match a job."""

        try:
            jobid = int(os.path.basename(name).split('_', 1)[0])
            job = MapRenderingJob.objects.get(id=jobid)
            if name.startswith(os.path.join(www.settings.RENDERING_RESULT_PATH, job.files_prefix())):
                return job
        except (ValueError, IndexError, MapRenderingJob.DoesNotExist):
            pass

        return None

SPACE_REDUCE = re.compile(r"\s+")
NONASCII_REMOVE = re.compile(r"[^A-Za-z0-9]+")

class MapRenderingJob(models.Model):

    STATUS_LIST = (
        (0, 'Submitted'),
        (1, 'In progress'),
        (2, 'Done'),
        (3, 'Done w/o files'),
        (4, 'Cancelled'),
        )

    NONCE_SIZE = 16

    maptitle = models.CharField(max_length=256, null=True, blank=True)
    stylesheet = models.CharField(max_length=256)
    overlay = models.CharField(max_length=256, null=True, blank=True)
    layout = models.CharField(max_length=256)
    paper_width_mm = models.IntegerField()
    paper_height_mm = models.IntegerField()
    bitmap_dpi = models.IntegerField(default=72)

    # When rendering through administrative city is selected, the
    # following three fields must be non empty
    administrative_city = models.CharField(max_length=256, blank=True)
    administrative_osmid = models.IntegerField(blank=True, null=True)

    # When rendering through bounding box is selected, the following
    # four fields must be non empty
    lat_upper_left = models.FloatField(blank=True, null=True)
    lon_upper_left = models.FloatField(blank=True, null=True)
    lat_bottom_right = models.FloatField(blank=True, null=True)
    lon_bottom_right = models.FloatField(blank=True, null=True)

    status = models.IntegerField(choices=STATUS_LIST)
    submission_time = models.DateTimeField(auto_now_add=True)
    startofrendering_time = models.DateTimeField(null=True,blank=True)
    endofrendering_time = models.DateTimeField(null=True,blank=True)
    resultmsg = models.CharField(max_length=256, null=True,blank=True)
    submitterip = models.GenericIPAddressField(null=True,blank=True)
    submittermail = models.EmailField(null=True,blank=True)
    index_queue_at_submission = models.IntegerField()
    map_language = models.CharField(max_length=16)

    renderstep = models.CharField(max_length=80,null=True,blank=True)

    nonce = models.CharField(max_length=NONCE_SIZE, blank=True)

    class Meta:
        indexes = [models.Index(fields=['submission_time',]),]

    objects = MapRenderingJobManager()

    def __str__(self):
        return self.maptitle.encode('utf-8')

    def maptitle_computized(self):
        t = self.maptitle.strip()
        if self.id <= www.settings.LAST_OLD_ID:
            t = SPACE_REDUCE.sub("-", t)
            t = NONASCII_REMOVE.sub("", t)
        else:
            t = slugify(t)
        return t

    _files_prefix = None
    def files_prefix(self):
        if self._files_prefix is None:
            try:
                self._files_prefix = "%s/%06d_%s_%s" % \
                    (self.startofrendering_time.strftime("%Y/%m/%d"),
                     self.id,
                     self.startofrendering_time.strftime("%Y-%m-%d_%H-%M"),
                     self.maptitle_computized())
            except Exception:
                self._files_prefix = "%06d_%s" % \
                    (self.id,
                     self.maptitle_computized())
        return self._files_prefix

    def start_rendering(self):
        self.status = 1
        self.startofrendering_time = datetime.now()
        self.save()

    def end_rendering(self, resultmsg):
        self.status = 2
        self.endofrendering_time = datetime.now()
        self.resultmsg = resultmsg
        self.save()

    def rendering_time_gt_1min(self):
        if self.needs_waiting():
            return False

        delta = self.endofrendering_time - self.startofrendering_time
        return delta.seconds > 60

    def __is_ok(self):              return self.resultmsg == 'ok'

    def is_waiting(self):           return self.status == 0
    def is_rendering(self):         return self.status == 1
    def needs_waiting(self):        return self.status  < 2

    def is_done(self):              return self.status == 2
    def is_done_ok(self):           return self.is_done() and self.__is_ok()
    def is_done_failed(self):       return self.is_done() and not self.__is_ok()

    def is_obsolete(self):          return self.status == 3
    def is_obsolete_ok(self):       return self.is_obsolete() and self.__is_ok()
    def is_obsolete_failed(self):   return self.is_obsolete() and not self.__is_ok()

    def is_cancelled(self):         return self.status == 4

    def can_recreate(self):
        return (((self.administrative_city and self.administrative_osmid) or
                (self.lat_upper_left and self.lon_upper_left and
                 self.lat_bottom_right and self.lon_bottom_right)) and
                self.stylesheet and self.layout and
                self.paper_width_mm != -1 and self.paper_height_mm != -1)

    _map_fileurl_base = None
    def get_map_fileurl(self, format):
        if self._map_fileurl_base is None:
            self._map_fileurl_base = os.path.join(www.settings.RENDERING_RESULT_URL, self.files_prefix())
        return self._map_fileurl_base + format

    _map_filepath_base = None
    def get_map_filepath(self, format):
        if self._map_filepath_base is None:
            self._map_filepath_base = os.path.join(www.settings.RENDERING_RESULT_PATH, self.files_prefix() )
        return self._map_filepath_base + format

    def output_files(self):
        """Returns a structured dictionary of the output files for this job.
        The result contains two lists, 'maps' and 'indeces', listing the output
        files, and two single files for thumbnail and error output. 
        Each file is reported by a tuple (format, path, title, size)."""

        files_prefix = self.files_prefix()

        allfiles = {'maps': {}, 'indeces': {}, 'thumbnail': [], 'errorlog': []}

        formats = www.settings.RENDERING_RESULT_FORMATS
        formats.append('8bit.png')
        formats.append('jpg')
        for format in formats:
            map_path = self.get_map_filepath("." + format)
            if format != 'csv' and os.path.exists(map_path):
                # Map files (all formats but CSV)
                allfiles['maps'][format] = (
                    self.get_map_fileurl("." + format),
                    _("%(title)s %(format)s Map") % {'title': self.maptitle,
                                                     'format': format.upper()},
                    os.stat(map_path).st_size,
                    map_path)
            elif format == 'csv' and os.path.exists(map_path):
                # Index CSV file
                allfiles['indeces'][format] = (
                    self.get_map_fileurl(format),
                     _("%(title)s %(format)s Index") % {'title': self.maptitle,
                                                       'format': format.upper()},
                    os.stat(map_path).st_size,
                    map_path)

        thumbnail = self.get_map_filepath("_small.png")
        if os.path.exists(thumbnail):
            allfiles['thumbnail'].append(('thumbnail', None, os.stat(thumbnail).st_size, thumbnail))

        errorlog = self.get_map_filepath("-errors.txt")
        if os.path.exists(errorlog):
            allfiles['errorlog'].append(('errorlog', None, os.stat(errorlog).st_size, errorlog))

        return allfiles

    def has_output_files(self):
        """This function tells whether this job still has its output files
        available on the rendering storage.

        Their actual presence is checked if the job is considered done and not
        yet obsolete."""

        if self.is_done():
            files = self.output_files()
            return len(files['maps']) + len(files['indeces']) + len(files['thumbnail'])

        return False

    def remove_all_files(self):
        """Removes all the output files from this job, and returns the space
        saved in bytes (Note: the thumbnail is not removed)."""

        files = self.output_files()
        saved = 0
        removed = 0

        for f in (list(files['maps'].values()) + list(files['indeces'].values()) + files['thumbnail']):
            try:
                os.remove(f[3])
                removed += 1
                saved += f[2]
            except OSError:
                pass

        self.status = 3
        self.save()
        return removed, saved

    def cancel(self):
        self.status = 4
        self.endofrendering_time = datetime.now()
        self.resultmsg = 'rendering cancelled'
        self.save()

    def get_thumbnail(self):
        if self.is_waiting() or self.is_cancelled():
            return None

        thumbnail_file = os.path.join(www.settings.RENDERING_RESULT_PATH, self.files_prefix() + "_small.png")
        thumbnail_url = www.settings.RENDERING_RESULT_URL + "/" + self.files_prefix() + "_small.png"
        if os.path.exists(thumbnail_file):
            return thumbnail_url
        return None

    def get_errorlog(self):
        if self.is_waiting():
            return None

        errorlog_file = os.path.join(www.settings.RENDERING_RESULT_PATH, self.files_prefix() + "-errors.txt")
        errorlog_url = www.settings.RENDERING_RESULT_URL + "/" + self.files_prefix() + "-errors.txt"
        if os.path.exists(errorlog_file):
            return errorlog_url
        return None

    def get_errorlog_file(self):
        if self.is_waiting():
            return None

        errorlog_file = os.path.join(www.settings.RENDERING_RESULT_PATH, self.files_prefix() + "-errors.txt")

        if os.path.exists(errorlog_file):
            return errorlog_file
        return None

    def current_position_in_queue(self):
        return MapRenderingJob.objects.filter(status=0).filter(id__lte=self.id).count()

    # Estimate the date at which the rendering will be started
    def rendering_estimated_start_time(self):
        waiting_time = datetime.now() - self.submission_time
        progression = self.index_queue_at_submission - self.current_position_in_queue()
        if progression == 0:
            return datetime.now()
        mean_job_rendering_time = waiting_time // progression
        estimated_time_left = mean_job_rendering_time * self.current_position_in_queue()
        return datetime.now() + estimated_time_left

    def get_absolute_url(self):
        return reverse('map-by-id', args=[self.id])

    def clean(self):
        from django.core.exceptions import ValidationError
        import ocitysmap

        errors = {}

        _ocitysmap = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)
       
        renderer_names = _ocitysmap.get_all_renderer_names()
        if self.layout not in renderer_names:
            errors['layout'] = ValidationError(_("Invalid layout '%s'" % self.layout), code='invalid')

        style_names = _ocitysmap.get_all_style_names()
        if self.stylesheet not in style_names:
            errors['stylesheet'] = ValidationError(_("Invalid style '%s'" % self.stylesheet), code='invalid')

        # TODO Django form passes value in weird ways, check how to correctly do this ....
        if self.overlay is not None:
            LOG.warning("Overlays: %s" % self.overlay)
            overlay_names = _ocitysmap.get_all_overlay_names()
            if isinstance (self.overlay, str):
                overlays = self.overlay.split(',')
            else:
                overlays = self.overlay

#            for test_name in overlays:
#                LOG.warning("checking overlay '%s'" % test_name)
#                if test_name not in overlay_names:
#                    errors['overlay'] = ValidationError(_("Invalid overlay '%s'" % test_name), code='invalid')
#                    break

        if errors:
            raise ValidationError(errors)

class UploadFile(models.Model):
    FILE_TYPES = (
        ('gpx',  'GPX Track'),
        ('umap', 'UMAP Export File'),
        ('poi',  'POI File'),
        );

    uploaded_file = models.FileField(upload_to='upload/general/%Y/%m/%d/', null=True, blank=True)
    file_type = models.CharField(max_length = 4, choices = FILE_TYPES)

    job = models.ManyToManyField(MapRenderingJob, related_name = 'uploads')
