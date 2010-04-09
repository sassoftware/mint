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

class ManagedSystem(models.Model):
    parser = generateds_system.managedSystemType
    registrationDate = models.DateTimeField('Registration Date')
    generatedUUID = models.CharField(max_length=64, null=True)
    localUUID = models.CharField(max_length=64, null=True)
    sslClientCertificate = models.CharField(max_length=8092, null=True)
    sslClientKey = models.CharField(max_length=8092, null=True)
    sslServerCertificate = models.CharField(max_length=8092, null=True)

class SystemTarget(models.Model):
    managedSystem = models.ForeignKey(ManagedSystem, null=True)
    target = models.ForeignKey(rbuildermodels.Targets)
    targetSystemId = models.CharField(max_length=256, null=True)

class SoftwareVersion(models.Model):
    name = models.TextField()
    version = models.TextField()
    flavor = models.TextField()

    class Meta:
        unique_together = (('name', 'version', 'flavor'),)

class SystemSoftwareVersion(models.Model):
    managedSystem = models.ForeignKey(ManagedSystem)
    softwareVersion = models.ForeignKey(SoftwareVersion)

class SystemInformation(models.Model):
    managedSystem = models.ForeignKey(ManagedSystem)
    systemName = models.CharField(max_length=64, null=True)
    memory = models.IntegerField(null=True)
    osType = models.CharField(max_length=64, null=True)
    osMajorVersion = models.CharField(max_length=32, null=True)
    osMinorVersion = models.CharField(max_length=32, null=True)
    systemType = models.CharField(max_length=32, null=True)

class NetworkInformation(models.Model):
    managedSystem = models.ForeignKey(ManagedSystem)
    interfaceName = models.CharField(max_length=32, null=True)
    ipAddress = models.CharField(max_length=15, null=True)
    netmask = models.CharField(max_length=20, null=True)
    portType = models.CharField(max_length=32, null=True)

class StorageVolume(models.Model):
    managedSystem = models.ForeignKey(ManagedSystem)
    size = models.IntegerField(null=True)
    storageType = models.CharField(max_length=32, null=True)
    storageName = models.CharField(max_length=32, null=True)

class CPU(models.Model):
    managedSystem = models.ForeignKey(ManagedSystem)
    cpuType = models.CharField(max_length=64, null=True)
    cpuCount = models.IntegerField(null=True)
    cores = models.IntegerField(null=True)
    speed = models.IntegerField(null=True)
    enabled = models.NullBooleanField()
