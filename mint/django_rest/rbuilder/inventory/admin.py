#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.contrib import admin
from mint.django_rest.rbuilder.inventory import models as inventory_models

admin.site.register(inventory_models.System)
admin.site.register(inventory_models.Network)
admin.site.register(inventory_models.SystemLog)
admin.site.register(inventory_models.SystemLogEntry)

