#
# Copyright (c) 2010 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.opensource.org/licenses/cpl.php.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#

from mint.lib import data
from mint.lib import database

dbReader = database.dbReader
dbWriter = database.dbWriter

class ManagedSystemsTable(database.KeyedTable):
    name = 'managedSystems'
    key = 'managedSystemId'
    fields = [ 'managedSystemId',
               'versionTimeStamp' ]

class SystemsTargetsTable(database.DatabaseTable):
    name = 'systemsTargets'
    fields = [ 'managedSystemId', 
               'targetId' ]
