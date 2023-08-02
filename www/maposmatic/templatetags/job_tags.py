import www.settings

from .extratags import register

import os

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.html import escape

_alert_ok   = "<div class='alert alert-success' role='alert'>"
_alert_info = "<div class='alert alert-info'    role='alert'>"
_alert_warn = "<div class='alert alert-warning' role='alert'>"
_alert_err  = "<div class='alert alert-danger'  role='alert'>"
_alert_end  = "</div>"

def _lastline(filename):
    try:
        with open(filename, "rb") as file:
            file.seek(-2, os.SEEK_END)
            while file.read(1) != b'\n':
                file.seek(-2, os.SEEK_CUR)
            return str(file.readline().decode())
    except:
        return ""

@register.filter()
def job_status_to_str(value):
    if value.status == 0:
        return mark_safe(_alert_info + str(_("Waiting for rendering to begin...")) + _alert_end)
    elif value.status == 1:
        return mark_safe(_alert_info + str(_("The rendering is in progress...")) + _alert_end)
    elif value.status == 2:
        if value.resultmsg == 'ok':
            return mark_safe(_alert_ok + str(_("Rendering was successful.")) + _alert_end)
        else:
            # TODO properly templatize this
            result = _alert_err
            result+= "<h4><i class='fas fa-triangle-exclamation'></i> <b>%s!</b></h4>" % value.resultmsg # TODO localize the result messages

            if not value.resultmsg.startswith("Not enough memory"):
                error_log_tail = escape(_lastline(value.get_errorlog_file())).replace(':',':<br/>')
                if error_log_tail:
                    result+= _("Check the %(error_log)s for more details<br/>") % {
                        'error_log': "<a target='_blank' href='%s'><i class='fas fa-file-lines'></i> %s</a>" % (value.get_errorlog(), _("error log")),
                    }
                
                if www.settings.CONTACT_EMAIL:
                    if error_log_tail:
                        result+= "or "
                        result+= _("contact %(email)s for more information.") % {
                            'email': "<a href='mailto:%(email)s?subject=[MapOSMatic] Error on request %(id)d'><i class='fas fa-envelope'></i> %(email)s</a>" % {
                                "email": www.settings.CONTACT_EMAIL,
                                "id":    value.id
                            }
                        }
                    
                if error_log_tail:
                    result+= "<hr/><tt>%s</tt>" % error_log_tail
                    
            result += _alert_end

            return mark_safe(result)
    elif value.status == 3:
        if value.resultmsg == 'ok':
            return mark_safe(_alert_info + str(_("Rendering is obsolete: the rendering was successful, but the files are no longer available.")) + _alert_end)
        else:
            return mark_safe(_alert_warn + str(_("Obsolete failed rendering: the rendering failed, and the incomplete files have been removed.")) + _alert_end)
    elif value == 4:
        return mark_safe(_alert_warn + str(_("The rendering was cancelled by the user.")) + _alert_end)

    return ''


