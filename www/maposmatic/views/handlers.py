# Copyright (C) 2024  Hartmut Holzgraefe

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

import sys, traceback
import smtplib
import datetime
import html

import logging
LOG = logging.getLogger('maposmatic')

from django.shortcuts import render
from django.template.loader import render_to_string, get_template
from django.core import mail

import www.settings
from www.maposmatic import helpers, forms, models

def myhandler500(request):
    type, value, tb = sys.exc_info()

    tb_msg = "".join(traceback.format_exception(type, value, tb))

    template = get_template("frontend_email_exception.txt")

    context = { 'from':    www.settings.DAEMON_ERRORS_EMAIL_FROM,
                'replyto': www.settings.DAEMON_ERRORS_EMAIL_REPLY_TO,
                'to':      ', '.join(['%s <%s>' % admin for admin in www.settings.ADMINS]),
                'type':    type,
                'value':   value,
                'tb':      tb_msg,
                'url':     request.build_absolute_uri(),
                'method':  request.method,
                'date':    datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0200 (CEST)'),
               }

    body = template.render(context)
    subject = 'Web request exception caught'

    mail.mail_admins(subject, body)

    return render(request,
                  '500.html',
                  {
                      'LANGUAGE_CODE': www.settings.LANGUAGE_CODE,
                      'type': type,
                      'value': value,
                      'tb': tb_msg,
                   },
                  status = 500
                 )
