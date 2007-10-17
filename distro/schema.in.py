#!/usr/bin/python
import sys
sys.path.insert(0,'..')

from mint import schema, migrate
print "%d.%d" % (migrate.majorMinor(schema.RBUILDER_DB_VERSION.major))

