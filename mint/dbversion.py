#
# Copyright (c) 2005-2007 rPath, Inc.
# All rights reserved
#
import time

from mint import database

class VersionTable(database.KeyedTable):
    key = "version"
    name = "DatabaseVersion"
    fields = ['version']

