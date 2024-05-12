INSTALLATION NOTES
==================

Dependencies
------------

MapOSMatic depends on :

 * Python, the programming language.

 * OCitySMap, the rendering pipeline for MapOSMatic. See OCitySMap's
   install file for installation instructions and OCitySMap's
   dependencies.

 * Django, the Web framework used to develop the Web front-end, but
   also used for the maposmaticd daemon to conveniently access the
   database through Django's ORM.

 * The Django Cookie Law application for compliance with EU cookie
   regulations

 * python-psycopg2, to let Django access the PostgreSQL database.

 * python-feedparser, to parse the MapOSMatic blog feed and display
   the latest entries on the main MapOSMatic website.

 * python-imaging, to render PNG maps.

 * gettext, for internationalization.

 * JSON (any python-*json package should work).

 * ImageMagick, for rendering the thumbnails of multi-page maps.

On an Debian/Ubuntu installation, the following should be sufficient
to fullfil all basic MapOSMatic dependencies:

  sudo aptitude install python-django python-psycopg2 \
          python-feedparser python-imaging gettext imagemagick

You will also most likely need a working PostGIS installation for the
entire pipeline to run. See the INSTALL documentation of OcitySMap for
more details.

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
