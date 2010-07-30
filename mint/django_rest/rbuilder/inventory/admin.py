#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.contrib import admin
from rbuilder.inventory import models as inventory_models

admin.site.register(inventory_models.managed_system)
admin.site.register(inventory_models.system_network_information)
admin.site.register(inventory_models.system_log_entry)
admin.site.register(inventory_models.entry)

