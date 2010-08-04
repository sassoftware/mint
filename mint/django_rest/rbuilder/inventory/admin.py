#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.contrib import admin
from rbuilder.inventory import models as inventory_models

admin.site.register(inventory_models.ManagedSystem)
admin.site.register(inventory_models.Network)
admin.site.register(inventory_models.SystemLog)
admin.site.register(inventory_models.SystemLogEntry)

