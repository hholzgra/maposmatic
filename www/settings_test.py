# coding: utf-8

# Test settings for the MapOSMatic web front-end.
#
# Usage:
#     ./manage.py test --settings=www.settings_test
#
# This imports the normal settings and then overrides everything that would
# otherwise reach out to external services (databases, the blog feed, ...) or
# slow tests down.
#
# Like the normal settings, this still expects www/settings_local.py to be
# present -- but its *values* are irrelevant here, because everything the tests
# care about (databases, feed) is overridden below. In CI, create it once from
# the committed settings_local.py.dist template; nothing sensitive or
# host-specific is needed.

import os
import tempfile

# www.settings configures file logging at import time; make sure that lands in
# a writable location during tests instead of the production log path.
os.environ.setdefault(
    "MAPOSMATIC_LOG_FILE",
    os.path.join(tempfile.gettempdir(), "maposmatic-test.log"),
)

from www.settings import *  # noqa: F401,F403,E402

# Fast, isolated, dependency-free databases. The MapRenderingJob model has no
# PostgreSQL-only fields, so SQLite is fine for the model/unit tests. The
# raw-SQL GIS code paths (osm/flex/waymarked) are mocked in the tests that
# exercise them, so those aliases only need to *exist*, not to be real.
_SQLITE = {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
DATABASES = {
    "default":   dict(_SQLITE),
    "osm":       dict(_SQLITE),
    "flex":      dict(_SQLITE),
    "waymarked": dict(_SQLITE),
}

# Build the schema for the maposmatic app directly from the current models
# (run_syncdb) instead of replaying its migration history. Several historical
# migrations contain PostgreSQL-only raw SQL (e.g. `UPDATE ... FROM` with a
# table alias in 0026) that SQLite cannot parse, and replaying Postgres SQL on
# SQLite would not be a meaningful test anyway. Django's own apps keep their
# migrations. Migration-specific logic (e.g. the 0038 file_prefix backfill) is
# covered by testing its functions directly instead.
MIGRATION_MODULES = {"maposmatic": None}

# Never fetch the blog feed over the network while rendering templates.
FRONT_PAGE_FEED = ""

# Deterministic secret, and fast password hashing for any auth exercised.
SECRET_KEY = "test-only-not-a-real-secret"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

MAINTENANCE_MODE = False
