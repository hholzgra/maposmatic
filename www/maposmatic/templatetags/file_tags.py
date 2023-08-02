import os

import www.settings

from .extratags import register

@register.filter()
def file_basename(value):
    try:
      return os.path.basename(value.name)
    except:
      return ""

@register.filter()
def file_readable_size(value):
    path = os.path.join(www.settings.MEDIA_ROOT, value.name)
    if os.path.isfile(path):
        stats = os.stat(path)
        size  = stats.st_size

        for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
            if size < 1024.0:
                return "%.1f%s" % (size, unit)
            size = size / 1024

    else:
        return "not found"
