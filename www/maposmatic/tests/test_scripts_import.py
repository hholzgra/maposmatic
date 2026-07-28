# coding: utf-8

# Guard against import-order regressions in the standalone scripts.
#
# The render daemon runs as a systemd service -- i.e. in a fresh interpreter
# where django.setup() has NOT run yet. The test runner, by contrast, sets
# Django up before importing any test module, so importing the daemon
# *in-process* would NOT reproduce the real startup conditions. We therefore
# import it in a subprocess with a clean interpreter: if a model ends up
# imported before daemon.py calls setup() (as an over-eager flake8 "E402:
# import not at top of file" fix once did), Django raises AppRegistryNotReady
# and the subprocess exits non-zero.
#
# This is the one test that exercises the scripts/ startup chain, which the
# rest of the suite never touches. It is comparatively slow (~2s) because
# importing the daemon transitively imports render -> ocitysmap.

import os
import subprocess
import sys

from django.test import SimpleTestCase

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")


class DaemonImportSmokeTest(SimpleTestCase):
    def test_daemon_imports_in_a_fresh_interpreter(self):
        env = dict(os.environ, DJANGO_SETTINGS_MODULE="www.settings_test")
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, %r); import daemon" % SCRIPTS_DIR],
            cwd=REPO_ROOT, env=env, capture_output=True, text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            "daemon.py failed to import in a fresh interpreter "
            "(setup() must run before any model import):\n" + result.stderr,
        )
