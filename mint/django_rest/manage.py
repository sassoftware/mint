#!/usr/bin/env python

import os, sys

testutilsPath = os.environ.get('TESTUTILS_PATH', None)
if testutilsPath:
    sys.path.insert(0, testutilsPath)
    sys.path.insert(0, '../../../include')

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mint.django_rest.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
