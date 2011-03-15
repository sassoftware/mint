#
# Copyright (c) 2010, 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder import errors

class QuerySetError(errors.RbuilderError):
    pass

class QuerySetReadOnly(QuerySetError):
    "The %(querySetName)s Query Set can not be modified."
    status = 200
