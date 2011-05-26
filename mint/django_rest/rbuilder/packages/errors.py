#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder import errors

class PackageError(errors.RbuilderError):
    pass

class PackageActionNotEnabled(PackageError):
    "Action package type %(packageActionTypeName)s is not enabled for this resource."
    status = 200


