#!/usr/bin/python
import sys
sys.path.append('..')

from mint import database
print database.DatabaseTable.schemaVersion

