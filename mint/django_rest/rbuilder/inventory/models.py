#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

import datetime

from django.db import IntegrityError
from django.db import models

from rpath_models import Inventory, Schedule, System, SystemLogEntry, \
                         SystemLog

from mint.django_rest.rbuilder import models as rbuildermodels

class ModelParser(models.Model):
    """
    Common base class for models that exposes 2 class factories that are
    useful, and other methods to interact with the generic parser object for
    the model.

    The parser is generally a higher level, more abstract object, such as a
    system with all it's associated metadata such as software information and
    network information.

    Models are the individual django objects that represent the parser in the
    database in terms of individual tables. Such as a system table, with
    seperate tables for software information and network information.
    """

    # parser class that is associated with this model.
    parser = None


    class Meta:
        """Tells django not create schema for this model class."""
        abstract = True

    def __init__(self, *args, **kw):
        models.Model.__init__(self, *args, **kw)
        if not hasattr(self, 'parserInstance'):
            self.parserInstance = None
        # related models are all django models that can be created based on
        # the parser
        self.related_models = {}

    @classmethod
    def factoryParser(cls, parserInstance):
        """Create an instance of this model from a parser instance."""
        modelDict = cls._modelDict(parserInstance)
        inst = cls(**modelDict)
        inst.parserInstance = parserInstance
        return inst

    @classmethod
    def factoryDict(cls, **kw):
        """Create an instance of this model from a dictionary."""
        return cls(**kw)

    def populateRelatedModelsFromParser(self, parserInstance):
        """
        Populate all related models based on the values from  
        parserInstance.  
        """
        for relMod in self.related_models:
            modelDict = relMod._modelDict(parserInstance)
            inst = relMod(**modelDict)
            inst.parserInstance = parserInstance
            setattr(inst, self._meta.object_name, self)
            self.related_models[relMod] = inst

    def populateRelatedModelsFromDb(self, source=None):
        for relMod in self.related_models.keys():
            kwargs = {}
            if source:
                kwargs = {source._meta.object_name:source}
            else:
                kwargs = {self._meta.object_name:self}
            relObjs = relMod.objects.filter(**kwargs)
            if self.related_models[relMod] == []:
                self.related_models[relMod] = relObjs
            else:
                self.related_models[relMod] = relObjs[0]

    def saveRelatedModels(self):    
        for relModInst in self.related_models.values():
            if hasattr(relModInst, '__iter__'):
                for inst in relModInst:
                    inst.save()
            else:
                relModInst.save()

    def saveAll(self):
        """Saves this model instance itself and all related models."""
        ret = self.save()
        self.saveRelatedModels()
        return ret

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
        allModels = [self] + [v for v in self.related_models.values() \
                              if v is not None]
                                 
        listFields = {}
        fields = {}
        for mod in allModels:
            if hasattr(mod, '__iter__'):
                for m in mod:
                    listFields.setdefault(m.__class__.__name__, [])
                    listFields[m.__class__.__name__].append(m.getParser()) 
            else:
                for field in mod._meta.fields:
                    if not field.primary_key:
                        fields[field.name] = getattr(mod, field.name)
        parserAttrNames = [n.name for n in self.parser.member_data_items_]
        parserDict = {}
        for f, v in fields.items():
            if f in parserAttrNames:
                parserDict[f] = v

        parser = self.parser(**parserDict)
        for field, value in listFields.items():
            for v in value:
                getattr(parser, field).append(v)

        return parser

    @classmethod
    def _modelDict(cls, parserInstance, loadFields=False):
        """
        Return a dict of field names/values corrosponding to the values on
        parserInstance.  If loadFields is True, remove from the returned dict
        and fields not in cls.loadFields.  This allows for building a dict
        based on a known set of fields that we want to use to load a model
        from the db to check if that "instance" already exists in the db.
        """
        modelDict = dict((x.name, getattr(parserInstance, x.name)) \
                          for x in cls.parser.member_data_items_ \
                          if x.name in [n.name for n in cls._meta.fields])
        if loadFields:
            for key in modelDict.keys():
                if key not in cls.loadFields:
                    modelDict.pop(key)
        return modelDict

    @classmethod
    def loadFromDb(cls, parserInstance):
        """
        Return an instance of the model loaded from the database that
        corrosponds to parserInstance.  loadFields=True is passed to modelDict
        so that we only check those fields that we care about for seeing if an
        instance that matches the values on parserInstance already exists.
        """
        modelDict = cls._modelDict(parserInstance, loadFields=True)
        try:
            inst = cls.objects.get(**modelDict)
        except cls.DoesNotExist:
            return None
        except cls.MultipleObjectsReturned:
            # This should not happen. Somehow bad data got in the db.
            # Log the error and re-raise the exception.
            # TODO
            pass

        return inst
        
class UnmanagedModelParser(ModelParser):
    """
    This base class doesn't seem to be working, i.e., django still seems to
    want to create db tables for the models that inherit from the class.

    Don't use it for now.
    """
    class Meta:
        managed = False

class inventory(ModelParser):
    class Meta:
        managed = False
    parser = Inventory

class managed_system(ModelParser):
    parser = System
    activation_date = models.IntegerField('Activation Date', null=True)
    launch_date = models.IntegerField('Launch Date', null=True)
    generated_uuid = models.CharField(max_length=64, null=True)
    local_uuid = models.CharField(max_length=64, null=True)
    ssl_client_certificate = models.CharField(max_length=8092, null=True)
    ssl_client_key = models.CharField(max_length=8092, null=True)
    ssl_server_certificate = models.CharField(max_length=8092, null=True)
    scheduled_event_start_date = models.IntegerField(null=False)
    launching_user = models.ForeignKey(rbuildermodels.Users, null=True)
    available = models.BooleanField(null=False)
    description = models.CharField(max_length=8092, null=True)
    name = models.CharField(max_length=8092, null=True)

    loadFields = ['generated_uuid', 'local_uuid', 'ssl_client_certificate',
                  'ssl_client_key', 'ssl_server_certificate']

    def __init__(self, *args, **kw):
        ModelParser.__init__(self, *args, **kw)
        self.related_models[system_network_information] = None

    def getParser(self, request=None):
        parser = ModelParser.getParser(self)
        return parser

class state(ModelParser):
    state = models.CharField(max_length=8092)

class system_state(ModelParser):
    parser = System
    managed_system = models.ForeignKey(managed_system)
    state = models.ForeignKey(state)

class entry(ModelParser):
    entry = models.CharField(max_length=8092)

class system_log(ModelParser):
    parser = SystemLog
    managed_system = models.ForeignKey(managed_system)
    class Meta:
        managed = False

    def __init__(self, *args, **kw):
        ModelParser.__init__(self, *args, **kw)
        self.related_models[system_log_entry] = []

class system_log_entry(ModelParser):
    parser = SystemLogEntry 
    managed_system = models.ForeignKey(managed_system)
    entry = models.ForeignKey(entry)
    entry_date = models.IntegerField()

    def __init__(self, *args, **kw):
        ModelParser.__init__(self, *args, **kw)
        self.related_models[entry] = self.entry

class system_target(ModelParser):
    managed_system = models.ForeignKey(managed_system, null=True)
    target = models.ForeignKey(rbuildermodels.Targets, null=True)
    target_system_id = models.CharField(max_length=256, null=True)
    reservation_id = models.CharField(max_length=256, null=True)
    ip_address = models.CharField(max_length=15, null=True)
    public_dns_name = models.CharField(max_length=255, null=True)

class system_management_node(ModelParser):
    managed_system = models.ForeignKey('managed_system',
                        related_name='system_management_node_system_set')
    managed_node = models.ForeignKey('managed_system',
                        related_name='system_management_node_node_set')

class software_version(ModelParser):
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

class system_software_version(ModelParser):
    managed_system = models.ForeignKey(managed_system)
    software_version = models.ForeignKey(software_version)

    class Meta:
        unique_together = (('managed_system', 'software_version'),)

class system_information(ModelParser):
    managed_system = models.ForeignKey(managed_system)
    system_name = models.CharField(max_length=64, null=True)
    memory = models.IntegerField(null=True)
    os_type = models.CharField(max_length=64, null=True)
    os_major_version = models.CharField(max_length=32, null=True)
    os_minor_version = models.CharField(max_length=32, null=True)
    system_type = models.CharField(max_length=32, null=True)

class system_network_information(ModelParser):
    parser = System
    managed_system = models.ForeignKey(managed_system)
    interface_name = models.CharField(max_length=32, null=True)
    ip_address = models.CharField(max_length=15, null=True)
    netmask = models.CharField(max_length=20, null=True)
    port_type = models.CharField(max_length=32, null=True)
    public_dns_name = models.CharField(max_length=255, null=True)

class storage_volume(ModelParser):
    managed_system = models.ForeignKey(managed_system)
    size = models.IntegerField(null=True)
    storage_type = models.CharField(max_length=32, null=True)
    storage_name = models.CharField(max_length=32, null=True)

class cpu(ModelParser):
    managed_system = models.ForeignKey(managed_system)
    cpu_type = models.CharField(max_length=64, null=True)
    cpu_count = models.IntegerField(null=True)
    cores = models.IntegerField(null=True)
    speed = models.IntegerField(null=True)
    enabled = models.NullBooleanField()

class schedule(ModelParser):
    parser = Schedule
    schedule_id = models.AutoField(primary_key=True)
    schedule = models.CharField(max_length=4096, null=False)
    enabled = models.IntegerField(null=False)
    created = models.IntegerField(null=False)

class job_states(ModelParser):
    class Meta:
        managed = False
        db_table = 'job_states'
    job_state_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=1024, null=False)

class managed_system_scheduled_event(ModelParser):
    scheduled_event_id = models.AutoField(primary_key=True)
    state = models.ForeignKey(job_states, null=False)
    managed_system = models.ForeignKey(managed_system)
    schedule = models.ForeignKey(schedule)
    scheduled_time = models.IntegerField(null=True)

SYSTEM_ACTIVATED_LOG = "System activated via ractivate"
SYSTEM_MANUALLY_ACTIVATED_LOG = "System manually activated via rBuilder"
SYSTEM_POLLED_LOG = "System polled."
