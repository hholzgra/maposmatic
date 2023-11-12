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

import django
from django.urls import reverse
from django.db import connections
import django.utils.translation
import feedparser
import datetime
import git
import os

from .models import MapRenderingJob
import www.settings

from www.maposmatic import forms, models

import logging

LOG = logging.getLogger('maposmatic')

def get_latest_blog_posts():
    if not www.settings.FRONT_PAGE_FEED:
        return []
    f = feedparser.parse(www.settings.FRONT_PAGE_FEED)
    return f.entries[:4]

def get_osm_database_last_update():
    """Returns the timestamp of the last PostGIS database update, which is
    placed into the maposmatic_admin table in the PostGIS database by the
    planet-update incremental update script."""

    cursor = None

    try:
        cursor = connections['osm'].cursor()
        if cursor is None:
            return None

        cursor.execute("""select last_update from maposmatic_admin""")
        last_update = cursor.fetchone()
        if last_update is None or len(last_update) != 1:
            return None

        return last_update[0]
    except:
        pass
    finally:
        # Close the DB cursor if necessary
        if cursor is not None and not cursor.closed:
            cursor.close()

    return None

def get_waymarked_database_last_update():
    """Returns the timestamp of the last PostGIS database update, which is
    placed into the waymarked_admin table in the PostGIS database by the
    waymarked-update incremental update script."""

    cursor = None

    try:
        cursor = connections['waymarked'].cursor()
        if cursor is None:
            return None

        cursor.execute("""select min(date) from status""")
        last_update = cursor.fetchone()
        if last_update is None or len(last_update) != 1:
            return None

        return last_update[0]
    except:
        pass
    finally:
        # Close the DB cursor if necessary
        if cursor is not None and not cursor.closed:
            cursor.close()

    return None

def get_osmnames_table_ok():
    cursor = None

    try:
        cursor = connections['osm'].cursor()
        if cursor is None:
            return False

        cursor.execute("""select osm_id from place where name = 'Bielefeld'""")
        id = cursor.fetchone()
        if id is None or id[0] <= 0:
            return False

        return True
    except:
        pass
    finally:
        # Close the DB cursor if necessary
        if cursor is not None and not cursor.closed:
            cursor.close()

    return False

def queue_states():
    queues = {}

    for queue_name in www.settings.QUEUE_NAMES:
        status = {}
        status['running'] = www.settings.is_daemon_running(queue_name)
        status['size']    = models.MapRenderingJob.objects.queue_size(queue_name)
        queues[queue_name] = status

    return queues

def all_queues_running():
    for queue_name in www.settings.QUEUE_NAMES:
        if not www.settings.is_daemon_running(queue_name):
            return False
    return True

def queues_overall_state():
    queues_total = 0
    queues_running = 0
    for queue_name in www.settings.QUEUE_NAMES:
        queues_total = queues_total + 1
        if www.settings.is_daemon_running(queue_name):
            queues_running = queues_running + 1

    if queues_running == 0:
        return "danger"
    if queues_running < queues_total:
        return "warning"
    return "success"

def queues_overall_symbol():
    queues_total = 0
    queues_running = 0
    for queue_name in www.settings.QUEUE_NAMES:
        queues_total = queues_total + 1
        if www.settings.is_daemon_running(queue_name):
            queues_running = queues_running + 1

    if queues_running == 0:
        return "times"
    if queues_running < queues_total:
        return "exclamation"
    return "check"

def all(request):
    # Do not add the useless overhead of parsing blog entries when generating
    # the rss feed
    if request.path == reverse('rss-feed'):
        return {}

    l = django.utils.translation.get_language()
    if l in www.settings.PAYPAL_LANGUAGES:
        paypal_lang_code = www.settings.PAYPAL_LANGUAGES[l][0]
        paypal_country_code = www.settings.PAYPAL_LANGUAGES[l][1]
    else:
        paypal_lang_code = "en_US"
        paypal_country_code = "US"

    daemon_running = all_queues_running()

    gis_lastupdate = get_osm_database_last_update()
    gis_lag_ok = (gis_lastupdate
        and datetime.datetime.utcnow() - gis_lastupdate < datetime.timedelta(minutes=30)
        or False)

    waymarked_lastupdate = get_waymarked_database_last_update()
    waymarked_lag_ok = (waymarked_lastupdate 
        and datetime.datetime.utcnow() -  waymarked_lastupdate < datetime.timedelta(minutes=120)
        or False)

    osmnames_ok = get_osmnames_table_ok()

    if daemon_running and gis_lag_ok and waymarked_lag_ok:
        platform_status = 'check'
    elif daemon_running and gis_lastupdate and not (gis_lag_ok and waymarked_lag_ok):
        platform_status = 'triangle-exclamation'
    else:
        platform_status = 'hourglas-clock'

    try:
        git_repo = git.Repo(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) 
        git_branch = git_repo.active_branch
    except Exception as e:
        git_branch = e

    return {
        'BBOX_MAXIMUM_LENGTH_IN_METERS': www.settings.BBOX_MAXIMUM_LENGTH_IN_METERS,
        'BRAND_NAME':                    www.settings.BRAND_NAME,
        'CONTACT_CHAT':                  www.settings.CONTACT_CHAT,
        'CONTACT_EMAIL':                 www.settings.CONTACT_EMAIL,
        'DEBUG':                         www.settings.DEBUG,
        'EXTRA_FOOTER':                  www.settings.EXTRA_FOOTER,
        'GIT_BRANCH':                    git_branch,
        'LANGUAGES':                     www.settings.LANGUAGES,
        'LANGUAGES_LIST':                www.settings.LANGUAGES_LIST,
        'LANGUAGE_FLAGS':                www.settings.LANGUAGE_FLAGS,
        'MAINTENANCE_NOTICE':            www.settings.MAINTENANCE_NOTICE,
        'MAP_LANGUAGES':                 www.settings.MAP_LANGUAGES,
        'MAX_BOUNDING_BOX':              www.settings.MAX_BOUNDING_BOX,
        'OUTER_BOUNDS_JSON':             www.settings.MAX_BOUNDING_OUTER,
        'PAYPAL_ID':                     www.settings.PAYPAL_ID,
        'PIWIK_BASE_URL':                www.settings.PIWIK_BASE_URL,
        'SUBMITTER_IP_LIFETIME':         www.settings.SUBMITTER_IP_LIFETIME,
        'SUBMITTER_MAIL_LIFETIME':       www.settings.SUBMITTER_MAIL_LIFETIME,
        'WEBLATE_BASE_URL':              www.settings.WEBLATE_BASE_URL,

        'searchform':                    forms.MapSearchForm(request.GET),
        'blogposts':                     get_latest_blog_posts(),

        'daemon_running':                daemon_running,
        'gis_lastupdate':                gis_lastupdate,
        'gis_lag_ok':                    gis_lag_ok,
        'waymarked_lastupdate':          waymarked_lastupdate,
        'waymarked_lag_ok':              waymarked_lag_ok,
        'osmnames_ok':                   osmnames_ok,
        'utc_now':                       datetime.datetime.utcnow(),
        'platform_status':               platform_status,

        'paypal_lang_code':              paypal_lang_code,
        'paypal_country_code':           paypal_country_code,

        'queue_states':                  queue_states(),
        'queues_overall_state':          queues_overall_state(),
        'queues_overall_symbol':         queues_overall_symbol(),
    }
