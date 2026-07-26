MapOSMatic - A web interface for creating printable OpenStreetMap maps
======================================================================

MapOSMatic is a web application to generate maps of cities or towns,
including index of streets, from OpenStreetMap data.

It is made of two components:

 * MapOSMatic (this repository): the web front-end. An application
   written using the Django framework allows to submit and visualize
   map rendering jobs.
   The rendering is done in the background by a daemon process.

 * [OCitysMap](https://github.com/hholzgra/ocitysmap): the back-end 
   that generates the map. It is available as a Python module, used 
   both by the maposmatic daemon (above) and by a sample command 
   line application.

It is licensed under under GNU AGPLv3
(GNU Affero General Public License 3.0).

Translation
-----------

You can help translating the user interface into other languages here:

https://translate.get-map.org/projects/maposmatic/maposmatic/

Installation
------------

Please refer to the [``INSTALL``](INSTALL.md) file in this repository.

Running tests
-------------

The automated test suite runs against a dedicated, self-contained test
settings module (``www/settings_test.py``) that uses throwaway in-memory
SQLite databases, so it needs neither PostgreSQL nor any external service:

```bash
   ./manage.py test www.maposmatic --settings=www.settings_test
```

Like the normal settings, the test settings still expect a
``www/settings_local.py`` to exist, but none of its values matter for the
tests. In a fresh checkout (or CI) create one from the template first:

```bash
   cp www/settings_local.py.dist www/settings_local.py
```

Tests live in ``www/maposmatic/tests/``.

Pre-commit hook
---------------

The test suite can be run automatically before every commit via the
[pre-commit](https://pre-commit.com/) framework (configured in
``.pre-commit-config.yaml``). Enable it once per clone, from within the
activated virtualenv:

```bash
   pip install -r requirements-dev.txt
   pre-commit install
```

Afterwards ``git commit`` runs the test suite first and aborts the commit if
any test fails. Bypass a single commit with ``git commit --no-verify``.

End user and API documentation
------------------------------

End user documentation for the web frontends useage, and API documentation
for developers who want to submit their own rendering job into the rendering
daemons queue, can be found in the [``documentation``](documentation) subdirectory.
