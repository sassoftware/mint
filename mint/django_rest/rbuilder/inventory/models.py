#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#
import urlparse

from django.db import models
from django.db.models.fields import related
from django.core.urlresolvers import reverse

from mint.django_rest.rbuilder import models as rbuildermodels

from xobj import xobj

class TransientManager(models.Manager):
    _transient = True

class XObjModel(models.Model):
    objects = TransientManager()

    class Meta:
        abstract = True

    listFields = []

    def to_xml(self, request=None):
        self.serialize(request)
        return xobj.toxml(self, self.__class__.__name__)

    def get_absolute_uri(self, request=None):
        viewName = getattr(self, 'viewName', self.__class__.__name__)
        urlKey = getattr(self, 'pk', [])
        if urlKey:
            urlKey = [str(urlKey[0])]
        bits = (viewName, urlKey)
        relativeUrl = reverse(bits[0], None, *bits[1:3])
        if request:
            return request.build_absolute_uri(relativeUrl)
        else:
            return relativeUrl

    def get_specific_href(self, href, request=None):
        url = self.get_absolute_uri(request)
        return urlparse.urljoin(url, href)       

    def serialize(self, request=None):

        hrefFields = [(f, v) for f, v in self.__class__.__dict__.items() \
                        if isinstance(v, XObjHrefModel)]
        for href in hrefFields:
            setattr(self, href[0], self.get_specific_href(href[1].href, request))

        for field in self._meta.fields:
            if isinstance(field, related.RelatedField):
                self.__dict__[field.verbose_name] = \
                    XObjHrefModel(getattr(self, field.name).get_absolute_uri())

        for listField in self.listFields:
            for field in getattr(self, listField):
                field.serialize(request)

class XObjIdModel(XObjModel):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                attributes = ['id'])

    def serialize(self, request=None):
        XObjModel.serialize(self, request)
        self.id = self.get_absolute_uri(request)

class XObjHrefModel(XObjModel):
    _xobj = xobj.XObjMetadata(
                attributes = {'href':str})

    def __init__(self, href):
        self.href = href

    def serialize(self, request=None):
        XObjModel.serialize(self, request)
        self.href = self.get_specific_href(self.href, request)

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
    listFields = ['system']
    system = []

    def save(self):
        return [s.save() for s in self.system]

class System(XObjIdModel):
    class Meta:
        db_table = 'inventory_system'
    system_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=8092)
    created_date = models.DateTimeField(auto_now_add=True)
    # Launch date is nullable, we maay get it reported from the hypervisor or
    # physical target, we may not.
    launch_date = models.DateTimeField()
    target = models.ForeignKey(rbuildermodels.Targets, null=True)
    target_system_id = models.CharField(max_length=255, null=True)
    reservation_id = models.CharField(max_length=255, null=True)
    os_type = models.CharField(max_length=64, null=True)
    os_major_version = models.CharField(max_length=32, null=True)
    os_minor_version = models.CharField(max_length=32, null=True)

class ManagedSystem(XObjIdModel):
    class Meta:
        db_table = 'inventory_managed_system'
    managed_system_id = models.AutoField(primary_key=True)
    system = models.OneToOneField(System)
    activation_date = models.DateTimeField(auto_now_add=True)
    generated_uuid = models.CharField(max_length=64)
    local_uuid = models.CharField(max_length=64)
    ssl_client_certificate = models.CharField(max_length=8092)
    ssl_client_key = models.CharField(max_length=8092)
    ssl_server_certificate = models.CharField(max_length=8092)
    scheduled_event_start_date = models.DateTimeField()
    launching_user = models.ForeignKey(rbuildermodels.Users)
    available = models.BooleanField()
    description = models.CharField(max_length=8092)
    name = models.CharField(max_length=8092)
    STATE_CHOICES = (
        ('activated', 'Activated'),
        ('responsive', 'Responsive'),
        ('shut_down', 'Shut Down'),
        ('non-responsive', 'Non-Responsive'),
        ('dead', 'Dead'),
        ('mothballed', 'Mothballed'),
    )
    state = models.CharField(max_length=32, choices=STATE_CHOICES)
    versions = models.ManyToManyField('Version')
    management_node = models.ForeignKey('ManagementNode', null=True)
   
class SystemEventType(XObjIdModel):
    class Meta:
        db_table = 'inventory_system_event_type'
    system_event_type_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=8092, db_index=True)
    description = models.CharField(max_length=8092)
    
class SystemEvent(XObjIdModel):
    class Meta:
        db_table = 'inventory_system_event'
    system_event_id = models.AutoField(primary_key=True)
    system = models.ForeignKey(System, db_index=True)
    event_type = models.ForeignKey(SystemEventType)
    time_created = models.DateTimeField(auto_now_add=True)
    priority = models.SmallIntegerField(db_index=True)

# TODO: is this needed, or should we just use a recursive fk on ManagedSystem?
class ManagementNode(XObjModel):
    managed_system = models.OneToOneField(ManagedSystem)
    # TODO: what extra columns might we want to store about a management node,
    # if any?

class Network(XObjModel):
    class Meta:
        db_table = 'inventory_network'
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
    entries = models.ManyToManyField('LogEntry', through='SystemLogEntry',
        symmetrical=False)

class SystemLogEntry(XObjModel):
    class Meta:
        db_table = 'inventory_system_log_entry'
    system = models.ForeignKey(SystemLog)
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
