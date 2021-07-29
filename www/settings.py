# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2009  David Decotigny
# Copyright (C) 2009  Frédéric Lehobey
# Copyright (C) 2009  David Mentré
# Copyright (C) 2009  Maxime Petazzoni
# Copyright (C) 2009  Thomas Petazzoni
# Copyright (C) 2009  Gaël Utard
# Copyright (C) 2019  Hartmut Holzgraefe

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

# Django settings for www project.

import logging
import os.path

from django.utils.translation import ugettext_lazy as _

from .settings_local import *
try:
  from .settings_bounds import *
except ModuleNotFoundError:
  pass

from . import logconfig

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Berlin'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True


# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
# ADMIN_MEDIA_PREFIX = '/admin-media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'tm+wb)lp5q%br=p0d2toz&km_-w)cmcelv!7inons&^v9(q!d2'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_PATH, 'templates'),
            os.path.join(PROJECT_PATH, 'maposmatic/templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': True,
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'www.maposmatic.context_processors.all',
            ],
        },
    },
]

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'maintenance_mode.middleware.MaintenanceModeMiddleware',
)

ROOT_URLCONF = 'www.urls'

LOCAL_MEDIA_PATH = os.path.join(PROJECT_PATH, 'static')

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.staticfiles',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'cookielaw',
    'maintenance_mode',
    'www.maposmatic',
)

STATIC_URL = "/media/"
STATIC_ROOT = LOCAL_MEDIA_PATH

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Available website translations. Note that the language codes must be
# specified in Django i18n location (all lowercase, with the language and
# locale separated by a dash instead of an underscore: pt_BR -> pt-br)
LANGUAGES = {
    "ar":    "العربية",
    "be":    "беларуская",
    "ca":    "Català",
    "cs":    "Czech",
    "de":    "Deutsch",
    "el":    "ελληνικά",
    "en":    "English",
    "es":    "Español",
    "fa":    "فارسی",
    "fr":    "Français",
    "hr":    "Hrvatski",
    "hu":    "Hungarian",
    "id":    "Bahasa Indonesia",
    "it":    "Italiano",
    "ja":    "日本語",
    "nb":    "Norwegian Bokmål",
    "nl":    "Nederlands",
    "pl":    "Polski",
    "pt-br": "Português do Brasil",
    "pt-pt": "Português",
    "ru":    "Русский",
    "sk":    "Slovenčina",
    "tr":    "Türkçe",
    "uk":    "українська",
    "zh-tw": "繁體中文",
}
LANGUAGES_LIST = sorted(LANGUAGES.items(), key=lambda p: p[1])

LANGUAGE_FLAGS = {
    "ar":    "ar",
    "be":    "by",
    "ca":    "es-ct",
    "cs":    "cz",
    "de":    "de",
    "el":    "gr",
    "en":    "gb",
    "es":    "es",
    "fa":    "ir",
    "fr":    "fr",
    "hr":    "hr",
    "hu":    "hu",
    "id":    "id",
    "it":    "it",
    "ja":    "jp",
    "nb":    "no",
    "nl":    "nl",
    "pl":    "pl",
    "pt-br": "br",
    "pt-pt": "pt",
    "ru":    "ru",
    "sk":    "sk",
    "tr":    "tr",
    "uk":    "ua",
    "zh-tw": "tw",
}

LOCALE_PATHS = [
    os.path.join(PROJECT_PATH, 'locale')
]

# Associate a Django language code with:
#  the language code used to select the Paypal button
#  the country code that allows to get the proper translation of the
#  PayPal payment page
# When no association is found, we automatically default to english
PAYPAL_LANGUAGES = {
    "fr": ("fr_FR", "FR"),
    "de": ("de_DE", "DE"),
    "it": ("it_IT", "IT"),
    "pt-pt": ("pt_PT", "PT"),
    "pt-br": ("pt_BR", "BR"),
    "nl": ("nl_NL", "NL"),
    "pl": ("pl_PL", "PL"),
    "es": ("es_ES", "ES"),
    "el": ("el_GR", "GR"),
}

# Languages must be ordered by country (in xx_YY, YY is the country
# code), and then ordered with the most widely used language in the
# country first. For example, in France, we will want "French" to be
# the first, and catalan to be in the second place). The reason for
# this is that the order in the below list will be the order with
# which languages will be presented by the MapOSMatic website (after
# filtering the language list based on the country of the city that is
# being rendered).
MAP_LANGUAGES = {
    "ca_AD.UTF-8": "Andorra",
    "ar_AE.UTF-8": "دولة الإمارات العربية المتحدة",
    "en_AG":       "Antigua and Barbuda",
    "es_AR.UTF-8": "Argentina",
    "de_AT.UTF-8": "Österreich",
    "en_AU.UTF-8": "Australia",
    "nl_BE.UTF-8": "Koninkrijk België",
    "fr_BE.UTF-8": "Royaume de Belgique",
    "de_BE.UTF-8": "Königreich Belgien",
    "ar_BH.UTF-8": "البحرين",
    "be_BY.UTF-8": "Белару́сь",
    "es_BO.UTF-8": "Bolivia",
    "pt_BR.UTF-8": "Brasil",
    "en_BW.UTF-8": "Botswana",
    "en_CA.UTF-8": "Canada",
    "fr_CA.UTF-8": "Canada",
    "de_CH.UTF-8": "Schweiz",
    "fr_CH.UTF-8": "Suisse",
    "it_CH.UTF-8": "Svizzera",
    "el_GR.UTF-8": "Ελλάδα",
    "es_CL.UTF-8": "Chile",
    "es_CR.UTF-8": "Costa Rica",
    "de_DE.UTF-8": "Deutschland",
    "da_DK.UTF-8": "Danmark",
    "en_DK.UTF-8": "Denmark",
    "es_DO.UTF-8": "República Dominicana",
    "ar_DZ.UTF-8": "الجزائر",
    "es_EC.UTF-8": "Ecuador",
    "ar_EG.UTF-8": "مصر",
    "es_ES.UTF-8": "España",
    "ca_ES.UTF-8": "Espanya",
    "ast_ES.UTF-8": "España",
    "fr_FR.UTF-8": "France",
    "ca_FR.UTF-8": "França",
    "en_GB.UTF-8": "United Kingdom",
    "es_GT.UTF-8": "Guatemala",
    "en_HK.UTF-8": "Hong Kong",
    "es_HN.UTF-8": "Honduras",
    "hr_HR.UTF-8": "Republika Hrvatska",
    "id_ID.UTF-8": "Bahasa Indonesia",
    "en_IE.UTF-8": "Ireland",
    "en_IN":       "India",
    "ar_IQ.UTF-8": "العراق",
    "it_IT.UTF-8": "Italia",
    "ar_JO.UTF-8": "الأردنّ‎",
    "ar_KW.UTF-8": "الكويت",
    "ar_LB.UTF-8": "لبنان ",
    "ja_JP.UTF-8": "日本語",
    "fr_LU.UTF-8": "Luxembourg",
    "de_LU.UTF-8": "Luxemburg",
    "ar_LY.UTF-8": "ليبيا",
    "ar_MA.UTF-8": "المملكة المغربية",
    "es_MX.UTF-8": "México",
    "en_NG":       "Nigeria",
    "es_NI.UTF-8": "Nicaragua",
    "nl_NL.UTF-8": "Nederland",
    "nb_NO.UTF-8": "Norwegian Bokmål",
    "nn_NO.UTF-8": "Norwegian Nynorsk",
    "en_NZ.UTF-8": "New Zealand",
    "ar_OM.UTF-8": "سلطنة عمان",
    "es_PA.UTF-8": "Panamá",
    "es_PE.UTF-8": "Perú",
    "en_PH.UTF-8": "Philippines",
    "pl_PL.UTF-8": "Rzeczpospolita Polska",
    "pt_PT.UTF-8": "Portugal",
    "es_PR.UTF-8": "Puerto Rico",
    "es_PY.UTF-8": "Paraguay",
    "ar_QA.UTF-8": "دولة قطر",
    "ro_RO.UTF-8": "Românesc",
    "ru_RU.UTF-8": "Русский",
    "ar_SA.UTF-8": "المملكة العربية السعودية",
    "ar_SD.UTF-8": "السودان",
    "en_SG.UTF-8": "Singapore",
    "es_SV.UTF-8": "El Salvador",
    "ar_SY.UTF-8": "سوريا",
    "ar_TN.UTF-8": "تونس",
    "en_US.UTF-8": "United States",
    "es_US.UTF-8": "Estados Unidos de América",
    "uk_UA.UTF-8": "Україна",
    "es_UY.UTF-8": "Uruguay",
    "es_VE.UTF-8": "Venezuela",
    "ar_YE.UTF-8": "اليَمَن",
    "en_ZA.UTF-8": "South Africa",
    "en_ZW.UTF-8": "Zimbabwe",
    "tr_TR.UTF-8": "Türkçe",
    "sk_SK.UTF-8": "Slovakien",
    "hu_HU.UTF-8": "Hungarian",
    "fa_IR.UTF-8": "فارسی",
    "sq_AL.UTF-8": "Albanian",
    "sr_RS.UTF-8": "Serbian",
#    "C": _(u"No localization"),
}

MAP_LANGUAGES_LIST = sorted(MAP_LANGUAGES.items(), key=lambda p: p[1])
MAP_LANGUAGES_LIST.append(("C", _(u"No localization")))

# Job page refresh frequency, in seconds, for when the job is waiting in queue
# and when the job is currently being rendered.
REFRESH_JOB_WAITING = 15
REFRESH_JOB_RENDERING = 10

def is_daemon_running():
    return 0 == os.system('systemctl is-active maposmatic-render.service')

# Logging
logconfig.setup_maposmatic_logging(
        int(os.environ.get("MAPOSMATIC_LOG_LEVEL",
                           DEFAULT_MAPOSMATIC_LOG_LEVEL)),
        os.environ.get('MAPOSMATIC_LOG_FILE', DEFAULT_MAPOSMATIC_LOG_FILE),
        os.environ.get("MAPOSMATIC_LOG_FORMAT", DEFAULT_MAPOSMATIC_LOG_FORMAT))
LOG = logging.getLogger('maposmatic')

# File upload settings

# make sure that files that exceed FILE_UPLOAD_MAX_MEMORY_SIZE
# are still readable 
FILE_UPLOAD_PERMISSIONS = 0o644

MAINTENANCE_MODE = False  # True or False, *NOT* None
MAINTENANCE_MODE_IGNORE_IP_ADDRESSES = ('217.146.146.90',)
MAINTENANCE_MODE_TEMPLATE = '503.html'
