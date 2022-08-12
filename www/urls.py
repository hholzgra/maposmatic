#!/usr/bin/python
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
from django.conf.urls import include
from django.urls import re_path
from django.views.static import serve
from django.views.generic import TemplateView
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from .maposmatic import feeds
from .maposmatic import views
from .maposmatic import apis

from . import settings

urlpatterns = [
    re_path(r'^$',
        views.index,
        name='main'),

    re_path(r'^new/$',
        views.new,
        name='new'),
    re_path(r'^recreate/$',
        views.recreate,
        name='recreate'),
    re_path(r'^cancel/$',
        views.cancel,
        name='cancel'),

    re_path(r'^maps/(?P<id>\d+)/(?P<nonce>[A-Za-z]{16})$',
        views.map_full,
        name='map-by-id-and-nonce'),
    re_path(r'^maps/(?P<id>\d+)$',
        views.map_full,
        name='map-by-id'),
    re_path(r'^maps/(?P<category>[a-z]+)$',
        views.maps,
        name='maps-list-cagetory'),
    re_path(r'^maps/$',
        views.maps,
        name='maps'),

    re_path(r'^about/api/$',
        views.documentation_api,
        name='documentation_api'),
    re_path(r'^about/user-guide/$',
        views.documentation_user_guide,
        name='documentation_user_guide'),
    re_path(r'^about/$',
        views.about,
        name='about'),
    
    re_path(r'^privacy/$',
        views.privacy,
        name='privacy'),

    re_path(r'^donate/$',
        views.donate,
        name='donate'),
    re_path(r'^donate-thanks/$',
        views.donate_thanks,
        name='donate-thanks'),

    # API calls used by the web frontend
    # url(r'^apis/nominatim/$', views.api_nominatim),
    re_path(r'^apis/nominatim/$', views.api_geosearch),
    re_path(r'^apis/reversegeo/([^/]*)/([^/]*)/$', views.api_postgis_reverse),
    re_path(r'^apis/papersize', views.api_papersize),
    re_path(r'^apis/boundingbox/([^/]*)/$', views.api_bbox),
    re_path(r'^apis/polygon/([^/]*)/$',     views.api_polygon),
    re_path(r'^apis/rendering-status/([^/]*)$', views.api_rendering_status),

    # API calls for direct clients

    # unversioned
    re_path(r'^apis/paper_formats',         apis.paper_formats),
    re_path(r'^apis/layouts',               apis.layouts),
    re_path(r'^apis/styles',                apis.styles),
    re_path(r'^apis/overlays',              apis.overlays),
    re_path(r'^apis/job-stati',             apis.job_stati),
    re_path(r'^apis/jobs$',                 apis.jobs),
    re_path(r'^apis/jobs/(\d*)$',           apis.jobs),

    # versioned
    re_path(r'^apis/v1/paper_formats',         apis.paper_formats),
    re_path(r'^apis/v1/layouts',               apis.layouts),
    re_path(r'^apis/v1/styles',                apis.styles),
    re_path(r'^apis/v1/overlays',              apis.overlays),
    re_path(r'^apis/v1/job-stati',             apis.job_stati),
    re_path(r'^apis/v1/jobs$',                 apis.jobs),
    re_path(r'^apis/v1/jobs/(\d*)$',           apis.jobs),

    # Feeds
    re_path(r'feeds/maps/$', feeds.MapsFeed(), name='rss-feed'),
    re_path(r'feeds/errors/$', feeds.ErrorFeed(), name='error-feed'),

    # Internationalization
    re_path(r'^i18n/', include('django.conf.urls.i18n')),

    # robots.txt
    re_path(r'^robots\.txt$', TemplateView.as_view(template_name="robots.txt", content_type='text/plain')),

    # favicons 
    re_path(r'^favicon\.png$', RedirectView.as_view(url=staticfiles_storage.url('img/favicon.png'))),
    re_path(r'^favicon\.ico$', RedirectView.as_view(url=staticfiles_storage.url('img/favicon.ico'))),
    re_path(r'^apple-touch-icon.*\.png$', RedirectView.as_view(url=staticfiles_storage.url('img/apple-touch-icon.png'))),

    # test
    re_path(r'heatmap/', TemplateView.as_view(template_name='heatmap.html', content_type='text/html')),
    re_path(r'^apis/heatdata.js$',     apis.heatdata),
]

if settings.DEBUG:
    urlpatterns.append(
        re_path(r'^results/(?P<path>.*)$', serve,
         {'document_root': settings.RENDERING_RESULT_PATH}))

    urlpatterns.append(
        re_path(r'^media/(?P<path>.*)$', serve,
         {'document_root': settings.LOCAL_MEDIA_PATH}))
