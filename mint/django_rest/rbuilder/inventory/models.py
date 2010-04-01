#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

from django.db import models

from xml_1_0 import system

class Systems(models.Model):
    parser = system.systemTypeSub
    registrationDate = models.DateTimeField('Registration Date')
    generatedUUID = models.CharField(max_length=64)
    localUUID = models.CharField(max_length=64)
    systemName = models.CharField(max_length=64, null=True)
    memory = models.IntegerField(null=True)
    osType = models.CharField(max_length=64, null=True)
    osMajorVersion = models.CharField(max_length=32, null=True)
    topLevelGroup = models.CharField(max_length=64, null=True)
    osMinorVersion = models.CharField(max_length=32, null=True)
    flavor = models.CharField(max_length=32, null=True)
    systemType = models.CharField(max_length=32, null=True)
    sslClientCertificate = models.CharField(max_length=8092)
    sslClientKey = models.CharField(max_length=8092)
    sslServerCertificate = models.CharField(max_length=8092)

class NetworkInformation(models.Model):
    systemsId = models.ForeignKey(Systems)
    interfaceName = models.CharField(max_length=32, null=True)
    ipAddress = models.CharField(max_length=15, null=True)
    netmask = models.CharField(max_length=20, null=True)
    portType = models.CharField(max_length=32, null=True)

class StorageVolumes(models.Model):
    systemsId = models.ForeignKey(Systems)
    size = models.IntegerField(null=True)
    storageType = models.CharField(max_length=32, null=True)
    storageName = models.CharField(max_length=32, null=True)

class CPUs(models.Model):
    systemsId = models.ForeignKey(Systems)
    cpuType = models.CharField(max_length=64, null=True)
    cpuCount = models.IntegerField(null=True)
    cores = models.IntegerField(null=True)
    speed = models.IntegerField(null=True)
    enabled = models.NullBooleanField()
