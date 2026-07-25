INSTALLATION NOTES
==================

Dependencies
------------

MapOSMatic requires **Python 3.13** and depends on:

 * OCitySMap, the rendering pipeline for MapOSMatic. See OCitySMap's
   install file for installation instructions and its own (much larger,
   GIS-heavy) set of dependencies. MapOSMatic and OCitySMap are installed
   into the *same* Python virtualenv.

 * A set of Python packages, pinned in the ``requirements.txt`` file in
   this repository. Notable entries: Django (web framework, also used by
   the rendering daemon for ORM access to the database), psycopg2
   (PostgreSQL access), Django Cookie Law (EU cookie-consent compliance),
   Pillow (PNG map rendering), feedparser (blog feed on the front page),
   plus GitPython, gpxpy, requests, python-slugify, cachetools,
   django-ipware and django-multiupload.

 * A few non-Python system tools: ``gettext`` (internationalization),
   ``ImageMagick`` (its ``montage`` tool renders multi-page map
   thumbnails), and a working PostgreSQL/PostGIS installation.

Install the system tools and the build prerequisites for psycopg2
(which is built from source, so it needs libpq and a C compiler):

```bash
   sudo apt-get install gettext imagemagick \
                        postgresql postgis \
                        libpq-dev gcc python3-dev
```

Then create the virtualenv and install the pinned Python packages:

```bash
   python3 -m venv --system-site-packages /home/maposmatic
   /home/maposmatic/bin/pip install -r requirements.txt
```

The ``--system-site-packages`` flag lets the venv reuse system-provided
GIS Python bindings (e.g. python3-mapnik) that OCitySMap needs. See the
INSTALL documentation of OCitySMap for the full PostGIS / data import
setup, which the entire pipeline relies on.

Setup
-----

The ``www/`` directory contains the Django web application. The file
``www/settings_local.py.dist`` must be copied to ``www/settings_local.py``
and modified to match your installation configuration.

Likewise for ``www/maposmatic.wsgi.dist`` and ``scripts/config.py.dist``,
as well as ``www/maposmatic.wsgi`` and ``scripts/config.py``.

Some static files from django applications need to be copied into
the maposmatic static media directory:

```bash
   python3 manage.py collectstatic
```

The rendering database must then be initialized with the tables needed for
MapOSMatic, using :

```bash
   python3 manage.py migrate
```

The rendering daemon should be run in the background. It will fetch rendering
jobs from the database and put the results in a directory, as specified in the
``settings_local.py`` file.

To setup the daemon, you need to configure the wrapper in the ``scripts/``
directory by copying scripts/config.py-template to ``scripts/config.py`` and
editing it to match your setup. The wrapper will set the necessary environment
variables and paths for the daemon to run correctly.

Then, you can run the rendering daemon through the wrapper with:

```bash
   scripts/wrapper.py scripts/daemon.py &
```

You'll find in ``support/init-maposmaticd-template`` an init script
template that you can tweak and install on your machine to start the
MapOSMatic rendering daemon automatically at boot time. If you are not
using it or an equivalent, then please ignore any message "The
MapOSMatic rendering daemon is currently not running! [...]" that the
web frontend (below) might display.

Testing with Django integrated web server
-----------------------------------------

Before you think about configuring your web server to provide the
maposmatic services, you should try them locally first:

```bash
  ./manage.py runserver
```

Then point your web browser to the address mentioned in the output
message. You will need to adjust ``RENDERING_RESULT_URL`` in
``www/settings_local.py`` to something like
'http://localhost:8000/results' (8000 being the port that is assigned
to the integrated web server, printed on the console when you start
it), otherwise the rendered map files will not be accessible through
the web frontend.

External Web server configuration
---------------------------------

In a normal setup, you don't want to use the Django integrated web
server. If you are using Apache, you can adapt the configuration file
given in ``support/apache-maposmatic-template``.

Also double-check ``DEFAULT_MAPOSMATIC_LOG_FILE`` in ``www/settings_local.py``
is writable by the web server. For example:

```bash
  sudo chgrp www-data /path/to/maposmatic/logs/maposmatic.log
  sudo chmod 664 /path/to/maposmatic/logs/maposmatic.log
```

Internationalization
--------------------

To get proper internationalisation, you need to compile the gettext
locale files:

```bash
  cd www && django-admin compilemessages
```

Don't forget to restart the Django server or it won't pick up the new
translated strings.
