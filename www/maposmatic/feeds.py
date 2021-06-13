# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2010  David Decotigny
# Copyright (C) 2010  Frédéric Lehobey
# Copyright (C) 2010  Pierre Mauduit
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

# Feeds for MapOSMatic

import datetime
import logging

LOG = logging.getLogger('maposmatic')

from django.contrib.gis.feeds import Feed
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string, get_template

from www.maposmatic import models
import www.settings

class MapsFeed(Feed):
    """
    This feeds syndicates the latest successfully rendered maps in MapOSMatic,
    with their thumbnail, and links to the rendered files.
    """

    title = "%s %s %s" % (www.settings.BRAND_NAME, _("maps"), 
                          www.settings.DEBUG and '' or _('[DEV]'))
    link = '/maps/' # We can't use reverse here as the urlpatterns aren't
                    # defined yet at this point.
    description = _('The latest rendered maps on MapOSMatic.')

    description_template = "maposmatic/map-feed.html"

    def items(self):
        """Returns the successfully rendered maps from the last 24 hours, or
        the last 10 maps/jobs if nothing happened recently."""

        one_day_before = datetime.datetime.now() - datetime.timedelta(1)
        items = (models.MapRenderingJob.objects
                 .filter(status=2)
                 .filter(resultmsg='ok')
                 .filter(endofrendering_time__gte=one_day_before)
                 .order_by('-endofrendering_time'))

        if items.count():
            return items

        # Fall back to the last 10 entries, regardless of time
        return (models.MapRenderingJob.objects
                .filter(status=2)
                .filter(resultmsg='ok')
                .order_by('-endofrendering_time')[:10])

        # Not sure what to do if we still don't have any items at this point.

    def item_title(self, item):
        title = item.maptitle
        if not title:
            title = "(untitled)"
        return "#%d - %s" % (item.id, title)

    def item_geometry(self, item):
        if item.administrative_city:
            return None
        else:
            return (item.lon_upper_left, item.lat_upper_left,
                    item.lon_bottom_right, item.lat_bottom_right)

    def item_pubdate(self, item):
        return item.endofrendering_time;

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['MAP_LANGUAGES'] = www.settings.MAP_LANGUAGES
        return context


class ErrorFeed(Feed):
    """
    This feeds syndicates the latest failed render request in MapOSMatic
    """

    title = "%s %s %s" % (www.settings.BRAND_NAME, _("errors"),
                          www.settings.DEBUG and '' or _('[DEV]'))
    link = '/maps/' # We can't use reverse here as the urlpatterns aren't
                    # defined yet at this point.
    description = _('The latest render failures on MapOSMatic.')

    # description_template = "maposmatic/map-feed.html"

    def items(self):
        """Returns the rendering failures from the last week, or
        the last 10 failures if nothing happened recently."""

        one_day_before = datetime.datetime.now() - datetime.timedelta(7)
        items = (models.MapRenderingJob.objects
                 .filter(status=2)
                 .exclude(resultmsg='ok')
                 .filter(endofrendering_time__gte=one_day_before)
                 .order_by('-endofrendering_time'))

        if items.count():
            return items

        # Fall back to the last 10 entries, regardless of time
        return (models.MapRenderingJob.objects
                .filter(status=2)
                .exclude(resultmsg='ok')
                .order_by('-endofrendering_time')[:10])

        # Not sure what to do if we still don't have any items at this point.

    def item_title(self, item):
        return item.maptitle

    def item_description(self, item):
        try:
            errortext = open(item.get_errorlog_file(), 'r').read()
        except:
            errortext = 'no error file found'
        return "<strong>%s</strong><hr/><pre>%s</pre>" % (item.resultmsg, errortext)

    def item_geometry(self, item):
        if item.administrative_city:
            return None
        else:
            return (item.lon_upper_left, item.lat_upper_left,
                    item.lon_bottom_right, item.lat_bottom_right)

    def item_pubdate(self, item):
        return item.startofrendering_time;
