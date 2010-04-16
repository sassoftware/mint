#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.db import IntegrityError
from django.db import models
from django.db import transaction

from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import generateds_system

class managed_system(models.Model):
    parser = generateds_system.managedSystemType
    registration_date = models.DateTimeField('Registration Date')
    generated_UUID = models.CharField(max_length=64, null=True)
    local_UUID = models.CharField(max_length=64, null=True)
    ssl_client_certificate = models.CharField(max_length=8092, null=True)
    ssl_client_key = models.CharField(max_length=8092, null=True)
    ssl_server_certificate = models.CharField(max_length=8092, null=True)
    launching_user = models.ForeignKey(rbuildermodels.Users, null=True)

class system_target(models.Model):
    managed_system = models.ForeignKey(managed_system, null=True)
    target = models.ForeignKey(rbuildermodels.Targets)
    target_system_id = models.CharField(max_length=256, null=True)

class software_version(models.Model):
    name = models.TextField()
    version = models.TextField()
    flavor = models.TextField()

    class Meta:
        unique_together = (('name', 'version', 'flavor'),)

class system_software_version(models.Model):
    managed_system = models.ForeignKey(managed_system)
    software_version = models.ForeignKey(software_version)

class system_information(models.Model):
    managed_system = models.ForeignKey(managed_system)
    system_name = models.CharField(max_length=64, null=True)
    memory = models.IntegerField(null=True)
    os_type = models.CharField(max_length=64, null=True)
    os_major_version = models.CharField(max_length=32, null=True)
    os_minor_version = models.CharField(max_length=32, null=True)
    system_type = models.CharField(max_length=32, null=True)

class network_information(models.Model):
    managed_system = models.ForeignKey(managed_system)
    interface_name = models.CharField(max_length=32, null=True)
    ip_address = models.CharField(max_length=15, null=True)
    netmask = models.CharField(max_length=20, null=True)
    port_type = models.CharField(max_length=32, null=True)

class storage_volume(models.Model):
    managed_system = models.ForeignKey(managed_system)
    size = models.IntegerField(null=True)
    storage_type = models.CharField(max_length=32, null=True)
    storage_name = models.CharField(max_length=32, null=True)

class cpu(models.Model):
    managed_system = models.ForeignKey(managed_system)
    cpu_type = models.CharField(max_length=64, null=True)
    cpu_count = models.IntegerField(null=True)
    cores = models.IntegerField(null=True)
    speed = models.IntegerField(null=True)
    enabled = models.NullBooleanField()
