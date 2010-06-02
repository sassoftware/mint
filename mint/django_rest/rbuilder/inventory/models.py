#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import datetime

from django.db import IntegrityError
from django.db import models
from django.db import transaction

from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import generateds_system

class ModelParser(models.Model):
    """
    Common base class for models that exposes 2 class factories that are
    useful, and other methods to interact with the generic parser object for
    the model.
    """

    class Meta:
        """Tells django not create schema for this model class."""
        abstract = True

    def __init__(self, *args, **kw):
        models.Model.__init__(self, *args, **kw)
        if not hasattr(self, 'parserInstance'):
            self.parserInstance = None

    @classmethod
    def factoryParser(cls, parserInstance):
        """Create an instance of this model from a parser instance."""

        # Create a dictionary based on the attributes of parserInstance that
        # are known data items, as long as those data items are defined as
        # fields on the model.
        modelDict = dict((x.name, getattr(parserInstance, x.name)) \
                          for x in cls.parser.member_data_items_ \
                          if x.name in [n.name for n in cls._meta.fields])

        inst = cls(**modelDict)
        inst.parserInstance = parserInstance
        return inst

    @classmethod
    def factoryDict(cls, **kw):
        """Create an instance of this model from a dictionary."""
        return cls(**kw)

    def updateFromParser(self, parserInstance):
        """
        Updates the model's fields values based on the values from
        parserInstance, ignoring updating the primary key field as we don't
        want to overwrite this value with None.
        """
        fields = [n.name for n in self._meta.fields if n.primary_key is False]
        for fieldName in fields:
           setattr(self, fieldName, getattr(parserInstance, fieldName, None))

    def getParser(self):
        """
        Return an instance of the parser class that represents this model.
        
        Override this method to customize behavior for more complex models
        with relationships.
        """
        fieldNames = [n.name for n in self._meta.fields if n.primary_key is False]
        parserAttrNames = [n.name for n in self.parser.member_data_items_]
        parserDict = {}
        for f in fieldNames:
            if f in parserAttrNames:
                parserDict[f] = getattr(self, f, None)

        return self.parser(**parserDict)

class managed_system(ModelParser):
    parser = generateds_system.managed_system_type
    registration_date = models.DateTimeField('Registration Date',
                            default=datetime.datetime.now())
    generated_uuid = models.CharField(max_length=64, null=True)
    local_uuid = models.CharField(max_length=64, null=True)
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

class software_version_update(ModelParser):
    # Need to specify the model name for the ForeignKey field here in quotes,
    # since we're redefining software_version.
    software_version = models.ForeignKey('software_version',
                        related_name='software_version_update_software_version_set')
    # This column is nullable, which basically means that the last time an
    # update was checked for, none was found.
    available_update = models.ForeignKey('software_version',
                        related_name='software_version_update_available_update_set',
                        null=True)
    last_refreshed = models.DateTimeField(default=datetime.datetime.now())

    class Meta:
        unique_together = (('software_version', 'available_update'),)

class system_software_version(models.Model):
    managed_system = models.ForeignKey(managed_system)
    software_version = models.ForeignKey(software_version)

    class Meta:
        unique_together = (('managed_system', 'software_version'),)

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
