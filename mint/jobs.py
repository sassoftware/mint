#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#
from mint import database
from mint.mint_error import *

class BuildFilesTable(database.KeyedTable):
    name = 'BuildFiles'
    key = 'fileId'
    fields = ['fileId', 'buildId', 'idx', 'title', 'size', 'sha1' ]

class BuildFilesUrlsMapTable(database.KeyedTable):
    name = 'BuildFilesUrlsMap'
    key = 'fileId'
    fields = ['fileId', 'urlId']

class FilesUrlsTable(database.KeyedTable):
    name = 'FilesUrls'
    key = 'urlId'
    fields = ['urlId', 'urlType', 'url']
