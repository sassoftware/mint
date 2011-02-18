#
# Copyright (c) 2010, 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder import errors

class QuerySetError(errors.RbuilderError):
    pass

class AllSystemsQuerySetReadOnly(QuerySetError):
    "The All Systems Query Set can not be modified."
    stauts = 200
