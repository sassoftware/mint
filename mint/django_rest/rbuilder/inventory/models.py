#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#
import sys
import datetime
import urlparse

from django.db import models
from django.db.models.fields import related
from django.core import exceptions
from django.core.urlresolvers import reverse

from mint.django_rest.rbuilder import models as rbuildermodels

from xobj import xobj

class BaseManager(models.Manager):
    _transient = True

    def load(self, model_inst):
        self.model_inst = model_inst
    
    def get_by_natural_key(self, **kwargs):
        try:
            return self.get(**kwargs)
        except exceptions.ObjectDoesNotExist, e:
            self.model_inst.save()
            return self.model_inst

class XObjModel(models.Model):
    objects = BaseManager()

    class Meta:
        abstract = True

    list_fields = []

    def to_xml(self, request=None):
        self.serialize(request)
        return xobj.toxml(self, self.__class__.__name__)

    def get_absolute_url(self, request=None):
        view_name = getattr(self, 'view_name', self.__class__.__name__)
        url_key = getattr(self, 'pk', [])
        if url_key:
            url_key = [str(url_key)]
        bits = (view_name, url_key)
        relative_url = reverse(bits[0], None, *bits[1:3])
        if request:
            return request.build_absolute_uri(relative_url)
        else:
            return relative_url

    def get_specific_href(self, href, request=None):
        url = self.get_absolute_url(request)
        return urlparse.urljoin(url, href)       

    def serialize(self, request=None):

        href_fields = [(f, v) for f, v in self.__class__.__dict__.items() \
                        if isinstance(v, XObjHrefModel)]
        for href in href_fields:
            setattr(self, href[0], 
                    self.get_specific_href(href[1].href, request))

        for field in self._meta.fields:
            if isinstance(field, related.RelatedField):
                val = getattr(self, field.name, None)
                if val:
                    self.__dict__[field.verbose_name] = \
                        XObjHrefModel(getattr(self, field.name).get_absolute_url())

            if isinstance(field, models.DateTimeField):
                val = getattr(self, field.name, None)
                if val:
                    self.__dict__[field.name] = \
                        getattr(self, field.name).isoformat()

        for list_field in self.list_fields:
            for field in getattr(self, list_field):
                field.serialize(request)

    def __setattr__(self, attr, val):
        if attr in self._meta.get_all_field_names() or \
           attr.startswith('_'):
            super(XObjModel, self).__setattr__(attr, val)
        else:
            super(XObjModel, self).__setattr__(attr, val)
            self._to_set = getattr(self, '_to_set', {})
            self._to_set[attr] = val

    def set_related(self):
        for attr, val in self._to_set.items():
            if not val:
                continue
            rel_objs = self._meta.get_all_related_objects()
            for k, v in getattr(val, '__dict__', {}).items():
                for rel_obj in rel_objs:
                    if k == rel_obj.var_name:
                        getattr(self, rel_obj.get_accessor_name()).add(v)

            # for rel_obj, rel_mod in rel_objs:
                # if attr in rel_obj.opts.get_all_field_names():
                    # if not rel_mod:
                        # rel_mod = rel_obj.model()
                    # setattr(rel_mod, attr, val)
                    # getattr(self, rel_obj.get_accessor_name()).add(rel_mod)

class XObjIdModel(XObjModel):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                attributes = ['id'])

    def serialize(self, request=None):
        XObjModel.serialize(self, request)
        self.id = self.get_absolute_url(request)

class XObjHrefModel(XObjModel):
    _xobj = xobj.XObjMetadata(
                attributes = {'href':str})

    def __init__(self, href):
        self.href = href

    def serialize(self, request=None):
        XObjModel.serialize(self, request)
        self.href = self.get_specific_href(self.href, request)

class DateTimeXObjField(models.DateTimeField):
    _xobj = xobj.XObjMetadata()

    def __init__(self, *args, **kw):
        models.DateTimeField.__init__(self, *args, **kw)

    def __getattr__(self, attr):
        if attr == '_xobj':
            _xobj.text = getattr(self.model(), self.attname).isoformat()
            return self._xobj

class Inventory(XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'inventory',
                elements = ['systems', 'log'])
    systems = XObjHrefModel('systems/')
    log = XObjHrefModel('log/')

class Systems(XObjModel):
    class Meta:
        abstract = True
    list_fields = ['system']
    system = []

    def save(self):
        return [s.save() for s in self.system]

class SystemManager(BaseManager):

    def load(self, model_inst):
        super(SystemManager, self).load(model_inst)
        loaded_model = self.get_by_natural_key(
                        generated_uuid=model_inst.generated_uuid)
        if loaded_model:
            model_inst.pk = loaded_model.pk
        return model_inst

class System(XObjIdModel):
    objects = SystemManager()
    class Meta:
        db_table = 'inventory_system'
    _xobj = xobj.XObjMetadata(
                tag = 'system')
    system_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=8092)
    description = models.CharField(max_length=8092, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    # Launch date is nullable, we maay get it reported from the hypervisor or
    # physical target, we may not.
    launch_date = models.DateTimeField(null=True)
    target = models.ForeignKey(rbuildermodels.Targets, null=True)
    target_system_id = models.CharField(max_length=255, null=True)
    reservation_id = models.CharField(max_length=255, null=True)
    os_type = models.CharField(max_length=64, null=True)
    os_major_version = models.CharField(max_length=32, null=True)
    os_minor_version = models.CharField(max_length=32, null=True)
    activation_date = models.DateTimeField(auto_now_add=True)
    generated_uuid = models.CharField(max_length=64, unique=True, null=True)
    local_uuid = models.CharField(max_length=64, null=True)
    ssl_client_certificate = models.CharField(max_length=8092, null=True)
    ssl_client_key = models.CharField(max_length=8092, null=True)
    ssl_server_certificate = models.CharField(max_length=8092, null=True)
    scheduled_event_start_date = models.DateTimeField(null=True)
    launching_user = models.ForeignKey(rbuildermodels.Users, null=True)
    available = models.NullBooleanField()
    STATE_CHOICES = (
        ('activated', 'Activated'),
        ('responsive', 'Responsive'),
        ('shut_down', 'Shut Down'),
        ('non-responsive', 'Non-Responsive'),
        ('dead', 'Dead'),
        ('mothballed', 'Mothballed'),
    )
    state = models.CharField(max_length=32, choices=STATE_CHOICES, null=True)
    versions = models.ManyToManyField('Version', null=True)
    management_node = models.ForeignKey('ManagementNode', null=True,
                        related_name='system_set')
   
class SystemEventType(XObjIdModel):
    class Meta:
        db_table = 'inventory_system_event_type'
        
    POLL = "poll"
    POLL_PRIORITY = 50
    POLL_DESC = "standard polling event"
    
    POLL_NOW = "poll_now"
    POLL_NOW_PRIORITY = 90
    POLL_NOW_DESC = "on-demand polling event"
    
    ACTIVATION = "activation"
    ACTIVATION_PRIORITY = 100
    ACTIVATION_DESC = "on-demand activation event"
        
    system_event_type_id = models.AutoField(primary_key=True)
    EVENT_TYPES = (
        (ACTIVATION, ACTIVATION_DESC),
        (POLL_NOW, POLL_NOW_DESC),
        (POLL, POLL_DESC),
    )
    name = models.CharField(max_length=8092, db_index=True, choices=EVENT_TYPES)
    description = models.CharField(max_length=8092)
    priority = models.SmallIntegerField(db_index=True)
    
class SystemEvent(XObjIdModel):
    class Meta:
        db_table = 'inventory_system_event'
    system_event_id = models.AutoField(primary_key=True)
    system = models.ForeignKey(System, db_index=True)
    event_type = models.ForeignKey(SystemEventType)
    time_created = models.DateTimeField(auto_now_add=True)
    time_enabled = models.DateTimeField(default=datetime.datetime.utcnow())
    priority = models.SmallIntegerField(db_index=True)

# TODO: is this needed, or should we just use a recursive fk on ManagedSystem?
class ManagementNode(XObjModel):
    system = models.OneToOneField(System)
    # TODO: what extra columns might we want to store about a management node,
    # if any?

class Networks(XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='networks')
    list_fields = ['network']
    network = []

    def save(self):
        return [n.save() for n in network]

class Network(XObjModel):
    class Meta:
        db_table = 'inventory_network'
    _xobj = xobj.XObjMetadata(
                tag='network')
    network_id = models.AutoField(primary_key=True)
    system = models.ForeignKey(System)
    ip_address = models.IPAddressField()
    # TODO: how long should this be?
    ipv6_address = models.CharField(max_length=32, null=True)
    device_name = models.CharField(max_length=255) 
    public_dns_name = models.CharField(max_length=255)
    netmask = models.CharField(max_length=20, null=True)
    port_type = models.CharField(max_length=32, null=True)
    # TODO: add all the other fields we need about a network

class SystemLog(XObjModel):
    class Meta:
        db_table = 'inventory_system_log'
    system_log_id = models.AutoField(primary_key=True)
    system = models.ForeignKey(System)
    log_entries = models.ManyToManyField('LogEntry', through='SystemLogEntry',
        symmetrical=False)

class SystemLogEntry(XObjModel):
    class Meta:
        db_table = 'inventory_system_log_entry'
    system_log = models.ForeignKey(SystemLog)
    log_entry = models.ForeignKey('LogEntry')
    entry_date = models.DateTimeField(auto_now_add=True)

SYSTEM_ACTIVATED_LOG = "System activated via ractivate"
SYSTEM_MANUALLY_ACTIVATED_LOG = "System manually activated via rBuilder"
SYSTEM_POLLED_LOG = "System polled."
SYSTEM_FETCHED_LOG = "System data fetched."

class LogEntry(XObjModel):
    class Meta:
        db_table = 'inventory_log_entry'
    # TODO fill these out
    ENTRY_CHOICES = (
        (SYSTEM_ACTIVATED_LOG, SYSTEM_ACTIVATED_LOG),
        (SYSTEM_MANUALLY_ACTIVATED_LOG, SYSTEM_MANUALLY_ACTIVATED_LOG),
        (SYSTEM_POLLED_LOG, SYSTEM_POLLED_LOG),
        (SYSTEM_FETCHED_LOG, SYSTEM_FETCHED_LOG),
    )
    entry_id = models.AutoField(primary_key=True)
    entry = models.CharField(max_length=8092, choices=ENTRY_CHOICES)

class Version(XObjModel):
    class Meta:
        db_table = 'inventory_version'
        unique_together = (('name', 'version', 'flavor'),)
    version_id = models.AutoField(primary_key=True)
    name = models.TextField()
    version = models.TextField()
    flavor = models.TextField()
    available_updates = models.ManyToManyField('self',
        through='AvailableUpdate', symmetrical=False,
        related_name = 'availableUpdates_set')


class AvailableUpdate(XObjModel):
    class Meta:
        db_table = 'inventory_available_update'
        unique_together = (('software_version', 'available_update'),)
    software_version = models.ForeignKey(Version,
        related_name='softwareVersion_set')
    # This column is nullable, which basically means that the last time an
    # update was checked for, none was found.
    available_update = models.ForeignKey(Version,
        related_name = 'availableUpdate_set')
    last_refreshed = models.DateTimeField(auto_now_add=True)

type_map = {}
for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            type_map[mod_obj._xobj.tag] = mod_obj
            
    
#
# Ignore these for now
#
#class schedule(XObjModel):
#    schedule_id = models.AutoField(primary_key=True)
#    schedule = models.CharField(max_length=4096, null=False)
#    enabled = models.IntegerField(null=False)
#    created = models.IntegerField(null=False)
#
#class job_states(XObjModel):
#    class Meta:
#        managed = False
#        db_table = 'job_states'
#    job_state_id = models.AutoField(primary_key=True)
#    name = models.CharField(max_length=1024, null=False)
#
#class managed_system_scheduled_event(XObjModel):
#    scheduled_event_id = models.AutoField(primary_key=True)
#    state = models.ForeignKey(job_states, null=False)
#    managed_system = models.ForeignKey(managed_system)
#    schedule = models.ForeignKey(schedule)
#    scheduled_time = models.IntegerField(null=True)
