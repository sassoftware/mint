#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import sys
import re

from django.db import models
from django.db.backends import signals

from mint.django_rest import timeutils
from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder import errors
from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.projects.models import Project, ProjectVersion, Stage
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder.jobs import models as jobmodels
from mint.django_rest.rbuilder.inventory import zones as zmodels
from mint.django_rest.rbuilder.targets import models as targetmodels
from xobj import xobj
import logging

log = logging.getLogger(__name__)

Cache = modellib.Cache
XObjHidden = modellib.XObjHidden
APIReadOnly = modellib.APIReadOnly

def hasTemporaryTables(connection):
    drvname = connection.client.executable_name
    if drvname == 'sqlite3':
        # Bummer. sqlite3 won't report temp tables in sqlite_master, so django
        # won't report them in introspection.table_names
        cu = connection.cursor()
        ret = list(cu.execute("SELECT 1 FROM sqlite_temp_master WHERE type='table'"))
        return bool(ret)
    elif drvname == 'psql':
        return 'inventory_tmp' in connection.introspection.table_names()
    else:
        raise Exception("Unsupported driver")

def createTemporaryTables(connection=None, **kwargs):
    if not hasTemporaryTables(connection):
        cu = connection.cursor()
        cu.execute("""
            CREATE TEMPORARY TABLE inventory_tmp (
                res_id INTEGER NOT NULL,
                depth INTEGER NOT NULL
        )""")
# This registers the function to be executed when the connection is created
signals.connection_created.connect(createTemporaryTables)

class Pk(object):
    def __init__(self, pk):
        self.pk = pk

    def get_url_key(self, *args, **kwargs):
        return self.pk

class Inventory(modellib.XObjModel):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'inventory')

    zones = D(modellib.HrefField('zones'), "an entry point into the inventory management zones collection")
    management_nodes = D(modellib.HrefField('management_nodes'), "an entry point into the inventory management nodes collection (rPath Update Services)")
    system_types = D(modellib.HrefField('system_types'), "an entry point into the inventory system types collection")
    networks = D(modellib.HrefField('networks'), "an entry point into the inventory system networks collection")
    systems = D(modellib.HrefField('systems'), "an entry point into the collection of all systems (all systems in inventory_systems and infrastructure systems combined)")
    log = D(modellib.HrefField('log'), "an entry point into inventory logging")
    event_types = D(modellib.HrefField('event_types'), "an entry point into the inventory events collection")
    system_states = D(modellib.HrefField('system_states'), "an entry point into the inventory system states collection")
    job_states = D(modellib.HrefField('job_states'), "an entry point into the inventory job states collection")
    inventory_systems = D(modellib.HrefField('inventory_systems'), "an entry point into the collection of inventory systems (all systems visible in the UI under Systems)")
    infrastructure_systems = D(modellib.HrefField('infrastructure_systems'), "an entry point into the collection of infrastructure systems (all systems visible in the UI under Infrastructure)")

class Systems(modellib.Collection):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'systems')
    list_fields = ['system']
    system = []
    objects = modellib.SystemsManager()
    view_name = 'Systems'

    def __init__(self):
        modellib.Collection.__init__(self)

    def save(self):
        return [s.save() for s in self.system]

class SystemStates(modellib.XObjModel):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'system_states')
    list_fields = ['system_state']
    system_state = []

    def save(self):
        return [s.save() for s in self.system_state]

class ManagementNodes(modellib.XObjModel):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'management_nodes')
    list_fields = ['management_node']
    management_node = []

    objects = modellib.ManagementNodesManager()

    def save(self):
        return [s.save() for s in self.management_node]

class SystemsLog(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='systems_log')
    list_fields = ['system_log_entry']
    system_log_entry = []

class SystemEvents(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = 'system_events')
    list_fields = ['system_event']
    system_event = []

    def save(self):
        return [s.save() for s in self.system_event]

class Networks(modellib.XObjModel):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='networks',
                elements=['network', 'systems'])
    list_fields = ['network']

    systems = D(modellib.HrefField('../systems'), "an entry point into system inventory")


class SystemState(modellib.XObjIdModel):

    serialize_accessors = False
    class Meta:
        db_table = 'inventory_system_state'

    _xobj = xobj.XObjMetadata(
                tag = 'system_state',
                attributes = {'id':str})

    UNMANAGED = "unmanaged"
    UNMANAGED_DESC = "Unmanaged"

    UNMANAGED_CREDENTIALS_REQUIRED = "unmanaged-credentials"
    UNMANAGED_CREDENTIALS_REQUIRED_DESC = "Unmanaged: Invalid credentials"

    REGISTERED = "registered"
    REGISTERED_DESC = "Registered"

    RESPONSIVE = "responsive"
    RESPONSIVE_DESC = "Online"

    NONRESPONSIVE = "non-responsive-unknown"
    NONRESPONSIVE_DESC = "Not responding: Unknown"

    NONRESPONSIVE_NET = "non-responsive-net"
    NONRESPONSIVE_NET_DESC = "Not responding: Network unreachable"

    NONRESPONSIVE_HOST = "non-responsive-host"
    NONRESPONSIVE_HOST_DESC = "Not responding: Host unreachable"

    NONRESPONSIVE_SHUTDOWN = "non-responsive-shutdown"
    NONRESPONSIVE_SHUTDOWN_DESC = "Not responding: Hhutdown"

    NONRESPONSIVE_SUSPENDED = "non-responsive-suspended"
    NONRESPONSIVE_SUSPENDED_DESC = "Not responding: Suspended"

    NONRESPONSIVE_CREDENTIALS = "non-responsive-credentials"
    NONRESPONSIVE_CREDENTIALS_DESC = "Not responding: Invalid credentials"

    DEAD = "dead"
    DEAD_DESC = "Stale"

    MOTHBALLED = "mothballed"
    MOTHBALLED_DESC = "Retired"

    STATE_CHOICES = (
        (UNMANAGED, UNMANAGED_DESC),
        (UNMANAGED_CREDENTIALS_REQUIRED, UNMANAGED_CREDENTIALS_REQUIRED_DESC),
        (REGISTERED, REGISTERED_DESC),
        (RESPONSIVE, RESPONSIVE_DESC),
        (NONRESPONSIVE, NONRESPONSIVE_DESC),
        (NONRESPONSIVE_NET, NONRESPONSIVE_NET_DESC),
        (NONRESPONSIVE_HOST, NONRESPONSIVE_HOST_DESC),
        (NONRESPONSIVE_SHUTDOWN, NONRESPONSIVE_SHUTDOWN_DESC),
        (NONRESPONSIVE_SUSPENDED, NONRESPONSIVE_SUSPENDED_DESC),
        (NONRESPONSIVE_CREDENTIALS, NONRESPONSIVE_CREDENTIALS_DESC),
        (DEAD, DEAD_DESC),
        (MOTHBALLED, MOTHBALLED_DESC),
    )

    system_state_id = D(models.AutoField(primary_key=True), "the database id for the state")
    name = D(models.CharField(max_length=8092, unique=True,
        choices=STATE_CHOICES), "the state name", short="The state name")
    description = D(models.CharField(max_length=8092),
            "the state description", short="The state description")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the state was created (UTC)")

    load_fields = [ name ]


class SystemTypes(modellib.XObjModel):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='system_types',
                elements=['system_type'])
    list_fields = ['system_type']

class SystemType(modellib.XObjIdModel):

    class Meta:
        db_table = 'inventory_system_type'
    _xobj = xobj.XObjMetadata(
                tag = 'system_type',
                attributes = {'id':str})

    # Don't inline all the systems now.  Do not remove this code!
    # See https://issues.rpath.com/browse/RBL-7372 for more info
    _xobj_hidden_accessors = set(['systems',])

    INVENTORY = "inventory"
    INVENTORY_DESC = "Inventory"
    INFRASTRUCTURE_MANAGEMENT_NODE = "infrastructure-management-node"
    INFRASTRUCTURE_MANAGEMENT_NODE_DESC = "rPath Update Service (Infrastructure)"

    CHOICES = (
        (INVENTORY, INVENTORY_DESC),
        (INFRASTRUCTURE_MANAGEMENT_NODE, INFRASTRUCTURE_MANAGEMENT_NODE_DESC),
    )

    system_type_id = D(models.AutoField(primary_key=True), "the database ID for the system type")
    name = D(APIReadOnly(models.CharField(max_length=8092, unique=True,
        choices=CHOICES)), "the name of the system type",
        short="The name of the system type")
    description = D(models.CharField(max_length=8092),
            "the description of the system type",
            short="The description of the system type")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the system type was added to inventory (UTC)")
    infrastructure = D(models.BooleanField(), "whether or not the system type is infrastructure")
    creation_descriptor = D(modellib.XMLField(), "the descriptor of available fields to create systems of this type")

    load_fields = [ name ]

class NetworkAddress(modellib.XObjModel):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
            tag = 'network_address',
    )
    address = D(models.CharField(max_length=8092),
        "The address to use for contacting the system")
    pinned = D(models.BooleanField(),
        "true if the address is pinned")

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (self.address == other.address and
                bool(self.pinned) == bool(other.pinned))


class System(modellib.XObjIdModel):

    class Meta:
        db_table = 'inventory_system'
        ordering = [ 'system_id' ]

    view_name = 'System'

    # XXX this is hopefully a temporary solution to not serialize the FK
    # part of a many-to-many relationship
    _xobj_hidden_accessors = set(['systemjob_set', 'target_credentials',
        'managementnode', 'jobsystem_set', 'tags'])
    _xobj_hidden_m2m = set(['jobs'])
    _xobj = xobj.XObjMetadata(
                tag = 'system',
                attributes = {'id':str},
                elements = ['networks', ])
    # avoid expanding launching_user as, for now, rpath_models can't
    # deal with it and registration is affected when set
    _xobj_summary_view_hide = [ 'launching_user' ]
    _queryset_resource_type = 'system'

    """
    networks - a collection of network resources exposed by the system
    system_events - a link to the collection of system events currently
    active on this sytem
    """
    # need our own object manager for dup detection
    objects = modellib.SystemManager()
    system_id = D(models.AutoField(primary_key=True),
        "the database ID for the system", short="System ID")
    name = D(models.CharField(max_length=8092),
        "the system name", short="System name")
    description = D(models.CharField(max_length=8092, null=True),
        "the system description", short="System description")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the system was added to inventory (UTC)")
    hostname = D(models.CharField(max_length=8092, null=True),
        "the system hostname", short="System hostname")
    # Launch date is nullable, we may get it reported from the hypervisor or
    # physical target, we may not.
    launch_date = D(modellib.DateTimeUtcField(null=True),
        "the date the system was deployed (only applies if system is on a "
        "virtual target)", short="System launch date")
    target = D(modellib.ForeignKey(targetmodels.Target, null=True,
        text_field="name", on_delete=models.SET_NULL),
        "the virtual target the system was deployed to (only applies if "
        "system is on a virtual target)")
    target_system_id = D(models.CharField(max_length=255,
            null=True),
        "the system ID as reported by its target (only applies if system is "
        "on a virtual target)", short="System target system ID")
    target_system_name = D(APIReadOnly(models.CharField(max_length=255,
            null=True)),
        "the system name as reported by its target (only applies if system "
        "is on a virtual target)", short="System target system name")
    target_system_description = D(APIReadOnly(models.CharField(max_length=1024,
            null=True)),
        "the system description as reported by its target (only applies if "
        "system is on a virtual target)", short="System target system description")
    target_system_state = D(APIReadOnly(models.CharField(max_length=64,
            null=True)),
        "the system state as reported by its target (only applies if system "
        "is on a virtual target)", short="System target system state")
    registration_date = D(modellib.DateTimeUtcField(null=True),
        "the date the system was registered in inventory (UTC)", short="System registration date")
    generated_uuid = D(models.CharField(max_length=64, null=True),
        "a UUID that is randomly generated", short="System UUID")
    local_uuid = D(models.CharField(max_length=64, null=True),
        "a UUID created from the system hardware profile", short="System local UUID")
    launching_user = D(modellib.ForeignKey(usersmodels.User, null=True,
        text_field="user_name", on_delete=models.SET_NULL),
        "the user that deployed the system (only applies if system is on a "
        "virtual target)")
    current_state = D(modellib.SerializedForeignKey(
            SystemState, null=True, related_name='systems'),
        "the current state of the system", short="System state")
    managing_zone = D(modellib.ForeignKey(zmodels.Zone, null=False,
            related_name='systems', text_field="name"),
        "a link to the management zone in which this system resides")
    jobs = models.ManyToManyField(jobmodels.Job, through="SystemJob") #, related_name='systems')
    state_change_date = XObjHidden(APIReadOnly(modellib.DateTimeUtcField(
        auto_now_add=True, default=timeutils.now())))
    event_uuid = D(XObjHidden(modellib.SyntheticField()),
        "a UUID used to link system events with their returned responses")
    boot_uuid = D(XObjHidden(modellib.SyntheticField()),
        "a UUID used for tracking systems registering at startup time")
    system_type = D(modellib.ForeignKey(SystemType, null=False,
        related_name='systems', text_field='description'),
        "the type of the system",
        short="The system type")
    project_branch_stage = D(APIReadOnly(modellib.DeferredForeignKey(Stage, null=True,
        db_column="stage_id", text_field='name', related_name="+",
        on_delete=models.SET_NULL)),
        "the project stage of the system")
    project_branch = D(APIReadOnly(modellib.DeferredForeignKey(ProjectVersion, null=True,
        db_column="major_version_id", text_field='name', related_name="systems",
        on_delete=models.SET_NULL)),
        "the project major version of the system")
    project = D(APIReadOnly(modellib.DeferredForeignKey(Project, null=True,
        text_field='short_name', related_name="+", on_delete=models.SET_NULL)),
        "the project of the system")
    network_address = D(NetworkAddress, "Network address for this system", short="System network address")
    actions = D(APIReadOnly(modellib.SyntheticField(jobmodels.Actions)),
        "actions available on the system")
    source_image = D(APIReadOnly(models.ForeignKey('images.Image', null=True,
         related_name='systems', on_delete=models.SET_NULL)),
         'rBuilder image used to deploy the system, if any')
    created_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name='+', db_column='created_by', on_delete=models.SET_NULL),
        "User who created system",
        short="System created by")
    modified_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name='+', db_column='modified_by', on_delete=models.SET_NULL),
        "User who last modified system",
        short="System last modified by")
    modified_date = D(modellib.DateTimeUtcField(null=True),
        "the date the system was last modified", short="System modified date")

    # Note the camel-case here. It is intentional, this is a field sent
    # only by catalog-service via rmake, to simplify creation of system
    # objects (otherwise we'd have to create networks too and we may
    # change the way we deal with them)
    dnsName = XObjHidden(modellib.SyntheticField())
    targetType = XObjHidden(modellib.SyntheticField())
    targetName = XObjHidden(modellib.SyntheticField())

    # these fields are derived from job & trove state
    # stored here so serialization speed is acceptable
    # call updateDerivedData() to recalculate
    has_running_jobs = D(APIReadOnly(models.BooleanField(default=False, null=False)), 'whether the system has running jobs', short="System running jobs")
    has_active_jobs = D(APIReadOnly(models.BooleanField(default=False, null=False)), 'whether the system has active (queued/unqueud) jobs', short='System active jobs')

    # FIXME: OUT OF DATE -- installed software no longer used, can purge some of this?
    # We need to distinguish between an <installed_software> node not being
    # present at all, and being present and empty
    new_versions = None
    lastJob = None
    oldModel = None

    def save(self, *args, **kw):
        if self.current_state_id is None:
            self.current_state = SystemState.objects.get(
                name = SystemState.UNMANAGED)
        if not self.name:
            self.name = self.hostname and self.hostname or ''
        if self.system_type_id is None:
            self.system_type = SystemType.objects.get(
                name = SystemType.INVENTORY)
        modellib.XObjIdModel.save(self, *args, **kw)
        self.createLog()
        self.createNetworks()

    def createLog(self):
        system_log, created = SystemLog.objects.get_or_create(system=self)
        if created:
            system_log.save()
        return system_log

    def _matchNetwork(self, address, **kwargs):
        ret = self.networks.filter(ip_address=address, **kwargs)
        if ret:
            return ret[0]
        ret = self.networks.filter(dns_name=address, **kwargs)
        if ret:
            return ret[0]
        return None

    def updateNetworks(self, networks):
        # This function is called when loading a system object from xobj
        # and merging it with an existing system. This only happens on a
        # POST
        valid = re.compile('^[a-zA-Z0-9:._-]+$')
        futureNetworks = {}
        for nw in networks:
            key = (nw.ip_address or nw.dns_name)
            if not key:
                continue
            if not valid.match(key):
                raise errors.InvalidData(msg="invalid hostname/DNS name %s" %
                    key)
            futureNetworks[key] = nw
        # Walk DB networks
        pinnedFound = False
        # RCE-985: order networks by IP address, with nulls being last
        # This makes sure we don't attempt to update the ip address and
        # trip over the uniq constraint
        # Unfortunately django doesn't know how to tell pgsql
        # 'order by ip_address nulls last', the workaround is to
        # fabricate a column that is sorted by first.
        q = self.networks.extra(select=dict(null1="ip_address is null"))
        # If two networks have the same ip address (or lack thereof),
        # then fall back to primary key ordering
        for nw in q.order_by('null1', 'ip_address', 'network_id'):
            key = (nw.ip_address or nw.dns_name)
            if nw.pinned:
                if not pinnedFound:
                    # This is the first pinned network in the db
                    pinnedFound = True
                    futureNetworks.pop(key, None)
                    continue
                # Second pinned network. Remove it
                nw.delete()
                # We may add it back as unpinned
            fnw = futureNetworks.pop(key, None)
            if fnw is None:
                # This network should disappear
                if nw.network_id is not None:
                    nw.delete()
                continue
            nw.ip_address = fnw.ip_address
            nw.dns_name = fnw.dns_name
            nw.device_name = fnw.device_name
            nw.save()
        # Everything else has to be added
        for nw in futureNetworks.values():
            nw.system = self
            nw.save()
        self.network_address = self.__class__.extractNetworkAddress(self)

    def createNetworks(self):
        # * self.network_address comes originally from the DB, and updated
        #   from the xobj model
        # * curNetAddr is the state of the network in the db, which may
        #   have been altered since we loaded the object.

        if self.network_address is not None:
            dnsName = self.network_address.address
            address = re.compile('^[a-zA-Z0-9:._-]+$')
            if dnsName and not re.match(address, dnsName):
                raise errors.InvalidData(msg="invalid hostname/DNS name")

        currentNw = self.__class__.extractNetworkToUse(self)
        curNetAddr = self.newNetworkAddress(currentNw)
        if self.network_address is None or curNetAddr == self.network_address:
            # This is calling the custom __eq__, and also covers
            # None==None
            return

        if self.network_address.pinned:
            # We only have to remove the pinned network address. The
            # client maintains the rest
            self.networks.filter(pinned=True).delete()
        else:
            self.networks.all().delete()


        nw = Network(system=self, dns_name=dnsName,
            pinned=self.network_address.pinned)
        nw.save()

    @property
    def isRegistrationIncomplete(self):
        """
        Return True if local_uuid is missing (due to possible bugs in
        rpath-tools).
        """
        return self.generated_uuid is not None and not bool(self.local_uuid)

    @property
    def isRegistered(self):
        """
        Return True is the system is registered
        """
        return (self.local_uuid is not None and self.generated_uuid is not None)

    @property
    def isNewRegistration(self):
        """
        Return True if this object is a new registration.
        Relies on the presence of oldModel, which is set when we de-serialize
        the XML from clients.
        """
        if not self.isRegistered:
            return False
        om = self.oldModel
        if om is None:
            return True
        # This should also cover the empty string case
        if not self._text(om, 'local_uuid') or not self._text(om, 'generated_uuid'):
            return True
        return False

    @classmethod
    def _text(cls, etreeModel, field):
        node = etreeModel.find(field)
        if node is None:
            return node
        return node.text

    _RunningJobStateIds = None
    @property
    def runningJobStateIds(self):
        if self._RunningJobStateIds is None:
            self.__class__._RunningJobStateIds = set(
                Cache.get(jobmodels.JobState, name=x).job_state_id
                    for x in [ jobmodels.JobState.RUNNING,
                        jobmodels.JobState.QUEUED ])
        return self.__class__._RunningJobStateIds

    def areJobsActive(self, iterable):
        for job in iterable:
            if job.job_state_id in self.runningJobStateIds:
                return True
        return False

    def hasRunningJobs(self):
        return bool(self.jobs.filter(job_state__name=jobmodels.JobState.RUNNING))

    _runningJobState = None
    @property
    def runningJobState(self):
        if self._runningJobState is None:
            self.__class__._runningJobState = \
                Cache.get(jobmodels.JobState, name=jobmodels.JobState.RUNNING)
        return self.__class__._runningJobState

    def areJobsRunning(self, jobs):
        return bool([j for j in jobs \
            if j.job_state_id == self.runningJobState.job_state_id])

    def updateDerivedData(self):
        # call this to update cached data about the system record, so that it does not
        # have to be called at serialization time.

        jobs = []
        # if system was not saved yet, self.system_id is None
        if self.system_id is not None:
            jobs = self.jobs.filter(job_state__job_state_id__in=self.runningJobStateIds)

        self.has_active_jobs  = self.areJobsActive(jobs)
        self.has_running_jobs = self.areJobsRunning(jobs)
        self.save()

    def serialize(self, request=None, **kwargs):

        # hide some data in collapsed collections
        summarize = getattr(self, '_summarize', False)

        self.network_address = self.__class__.extractNetworkAddress(self)
        etreeModel = modellib.XObjIdModel.serialize(self, request, **kwargs)

        class JobsHref(modellib.XObjIdModel):
            _xobj = xobj.XObjMetadata(tag='jobs',
                elements = ['queued_jobs', 'completed_jobs',
                    'running_jobs', 'failed_jobs'],
                attributes = {'id':str})

            def __init__(self, request, system):
                self.view_name = 'SystemJobs'
                self.id = self.get_absolute_url(request, parents=[system])
                self.view_name = 'SystemJobStateJobs'
                parents = [system, Cache.get(jobmodels.JobState,
                    name=jobmodels.JobState.QUEUED)]
                self.queued_jobs = modellib.XObjHrefModel(
                    self.get_absolute_url(request, parents=parents))

                parents = [system, Cache.get(jobmodels.JobState,
                    name=jobmodels.JobState.COMPLETED)]
                self.completed_jobs = modellib.XObjHrefModel(
                    self.get_absolute_url(request, parents=parents))

                parents = [system, Cache.get(jobmodels.JobState,
                    name=jobmodels.JobState.RUNNING)]
                self.running_jobs = modellib.XObjHrefModel(
                    self.get_absolute_url(request, parents=parents))

                parents = [system, Cache.get(jobmodels.JobState,
                    name=jobmodels.JobState.FAILED)]
                self.failed_jobs = modellib.XObjHrefModel(
                    self.get_absolute_url(request, parents=parents))
                self.view_name = None

        # old and busted slow way
        #
        if not summarize:
            self.serializeJobsHref(etreeModel, request)
        return etreeModel

    def serializeJobsHref(self, etreeModel, request):
        baseUrl = self.get_absolute_url(request, view_name='SystemJobs')
        et = etreeModel.makeelement('jobs', id=baseUrl)
        etreeModel.append(et)

        subelMap = [
                ('queued_jobs', jobmodels.JobState.QUEUED),
                ('completed_jobs', jobmodels.JobState.COMPLETED),
                ('running_jobs', jobmodels.JobState.RUNNING),
                ('failed_jobs', jobmodels.JobState.FAILED),
        ]
        for subelName, state in subelMap:
            parents = [self, Cache.get(jobmodels.JobState, name=state)]
            url = self.get_absolute_url(request, parents=parents, view_name='SystemJobStateJobs')
            et.append(et.makeelement(subelName, id=url))

    @classmethod
    def extractNetworkToUse(cls, system):
        trueSet = set([ "True", "true" ])
        if hasattr(system.networks, 'all'):
            networks = system.networks.all()
        else:
            networks = system.networks.network
            for net in networks:
                net.pinned = (net.pinned in trueSet)
                net.active = (net.active in trueSet)

        # first look for user pinned nets
        nets = [ x for x in networks if x.pinned ]
        if nets:
            return nets[0]

        # now look for a non-pinned active net
        nets = [ x for x in networks if x.active ]
        if nets:
            return nets[0]

        # If we only have one network, return that one and hope for the best
        if len(networks) == 1:
            return networks[0]
        return None

    @classmethod
    def extractNetworkAddress(cls, system):
        nw = cls.extractNetworkToUse(system)
        return cls.newNetworkAddress(nw)

    @classmethod
    def newNetworkAddress(cls, network):
        if network is None:
            return None
        pinned = network.pinned
        address = network.ip_address or network.dns_name

        return NetworkAddress(address=address, pinned=pinned)

    def computeSyntheticFields(self, sender, **kwargs):
        ''' Compute non-database fields.'''
        self._computeActions()

    def _computeActions(self):
        '''What actions are available on the system?'''
        self.actions = actions = jobmodels.Actions()
        actions.action = []
        return actions

    def hasSourceImage(self):
        return bool(getattr(self, 'source_image', None))

# ABSTRACT


class ManagementNode(System):

    class Meta:
        db_table = 'inventory_zone_management_node'
        ordering = [ 'system_id' ]
    _xobj = xobj.XObjMetadata(
                tag = 'management_node',
                attributes = {'id':str})
    view_name = 'ManagementNode'
    local = D(models.NullBooleanField(), "whether or not this management node is local to the rBuilder")
    zone = D(modellib.ForeignKey(zmodels.Zone, related_name='management_nodes'), "the zone the management node lives in")
    node_jid = D(models.CharField(max_length=64, null=True), "the Jabber ID the management node is using")
    load_fields = [ node_jid ]

    # ignore auto generated ptr from inheritance
    load_ignore_fields = ["system_ptr"]

    # need our own object manager for dup detection
    objects = modellib.ManagementNodeManager()

    def save(self, *args, **kw):
        self.system_type = SystemType.objects.get(
            name = SystemType.INFRASTRUCTURE_MANAGEMENT_NODE)
        System.save(self, *args, **kw)

    def _computeActions(self):
        # At least for now, management nodes don't expose actions
        pass

class SystemTargetCredentials(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_system_target_credentials'
        unique_together = [ ('system', 'credentials') ]

    system = modellib.ForeignKey(System, null=False,
        related_name = 'target_credentials')
    credentials = modellib.ForeignKey(targetmodels.TargetCredentials,
        null=False, related_name = 'systems')


class SystemEvent(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_system_event'
    _xobj = xobj.XObjMetadata(
                tag = 'system_event',
                attributes = {'id':str})

    system_event_id = models.AutoField(primary_key=True)
    system = modellib.DeferredForeignKey(System, db_index=True,
        related_name='system_events')
    event_type = modellib.DeferredForeignKey(jobmodels.EventType,
        related_name='system_events', db_column='job_type_id')
    time_created = modellib.DateTimeUtcField(auto_now_add=True)
    time_enabled = modellib.DateTimeUtcField(
        default=timeutils.now(), db_index=True)
    priority = models.SmallIntegerField(db_index=True)
    event_data = models.TextField(null=True)

    def dispatchImmediately(self):
        return self.event_type.priority >= jobmodels.EventType.ON_DEMAND_BASE

    def get_absolute_url(self, request, parents=None, *args, **kwargs):
        if parents:
            if isinstance(parents[0], jobmodels.EventType):
                self.view_name = 'SystemEventsByType'
            elif isinstance(parents[0], System):
                self.view_name = 'SystemsSystemEvent'
        return modellib.XObjIdModel.get_absolute_url(self, request,
            parents=parents, *args, **kwargs)

    def save(self, *args, **kw):
        if not self.priority:
            self.priority = self.event_type.priority
        modellib.XObjIdModel.save(self, *args, **kw)

class Network(modellib.XObjIdModel):

    class Meta:
        db_table = 'inventory_system_network'
        unique_together = (('system', 'dns_name', 'ip_address', 'ipv6_address'),)
        ordering = [ 'network_id' ]

    _xobj = xobj.XObjMetadata(
                tag='network',
                attributes = {'id':str})
    network_id = D(models.AutoField(primary_key=True), "the database ID for the network")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True), "the date the network was created (UTC)")
    system = D(modellib.ForeignKey(System, related_name='networks'), "documentation missing")
    ip_address = D(models.CharField(max_length=15, null=True), "the network IP address")
    # TODO: how long should this be?
    ipv6_address = D(models.CharField(max_length=32, null=True), "the network IPv6 address")
    device_name = D(models.CharField(max_length=255), "the network device name")
    dns_name = D(models.CharField(max_length=255, db_index=True), "the network DNS name")
    netmask = D(models.CharField(max_length=20, null=True), "the network netmask")
    port_type = D(models.CharField(max_length=32, null=True), "the network port type")
    active = D(models.NullBooleanField(), "whether or not this is the active network device on the system")
    pinned = D(models.NullBooleanField(db_column="required"), "whether or not a user has pinned this network device be the one used to manage the system")

    load_fields = [ip_address, dns_name]

    def natural_key(self):
        return self.ip_address, self.dns_name

    def save(self, *args, **kwargs):
        """
        Disallow saving of link-local IPs.
        FIXME: Additionally allow edge case where the ip_address field
        is missing but we want to save the model anyway.
        """
        if self.ip_address and self.ip_address.startswith(("169.254", "fe80:")):
            return
        return super(Network, self).save(*args, **kwargs)

class SystemLog(modellib.XObjIdModel):
    _xobj = xobj.XObjMetadata(
                tag='system_log')

    class Meta:
        db_table = 'inventory_system_log'
    system_log_id = D(models.AutoField(primary_key=True), "the database ID for the system log")
    system = D(modellib.DeferredForeignKey(System, related_name='system_log'), "a entry point to the system this log is for")

    def get_absolute_url(self, request, parents=None, *args, **kwargs):
        if not parents:
            parents = [self.system]
        if isinstance(parents[0], System):
            self.view_name = 'SystemLog'
        return modellib.XObjIdModel.get_absolute_url(self, request,
            parents=parents, *args, **kwargs)

class SystemLogEntry(modellib.XObjModel):
    _xobj = xobj.XObjMetadata(
                tag='system_log_entry')
    class Meta:
        db_table = 'inventory_system_log_entry'
        ordering = ['entry_date']

    ADDED = "System added to inventory"
    REGISTERED = "System registered via rpath-tools"
    MANUALLY_REGISTERED = "System manually registered via rBuilder"
    POLLED = "System polled."
    FETCHED = "System data fetched."
    choices = (
        (ADDED, ADDED),
        (REGISTERED, REGISTERED),
        (MANUALLY_REGISTERED, MANUALLY_REGISTERED),
        (POLLED, POLLED),
        (FETCHED, FETCHED),
    )

    system_log_entry_id = models.AutoField(primary_key=True)
    system_log = modellib.ForeignKey(SystemLog,
        related_name='system_log_entries')
    entry = models.CharField(max_length=8092, choices=choices)
    entry_date = modellib.DateTimeUtcField(auto_now_add=True)


class SystemJobs(modellib.XObjModel):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                tag = 'system_jobs')
    list_fields = ['job']
    job = []

class SystemJob(modellib.XObjModel):
    class Meta:
        db_table = 'inventory_system_job'
    # XXX This class should never be serialized directly, but unless an _xobj
    # field is added, we have no access to it from modellib
    _xobj = xobj.XObjMetadata(tag='__systemJob')
    system_job_id = models.AutoField(primary_key=True)
    system = modellib.ForeignKey(System)
    job = modellib.DeferredForeignKey(jobmodels.Job, unique=True,
        related_name='systems')
    event_uuid = XObjHidden(models.CharField(max_length=64, unique=True))

class JobSystem(modellib.XObjModel):
    class Meta:
        db_table = 'job_system'
    job = models.ForeignKey(rbuildermodels.Jobs, null=False)
    # Django will insist on removing entries from this table when removing a
    # system, and because there's no primary key, it will fail. So, for now,
    # we don't use a FK for system
    #system = models.ForeignKey(System, null=False)
    system_id = models.IntegerField(null=False)

class ErrorResponse(modellib.XObjModel):
    _xobj = xobj.XObjMetadata(
                tag='fault')
    class Meta:
        abstract = True
    code = models.TextField()
    message = models.TextField()
    traceback = models.TextField()
    product_code = models.TextField()

# ------------------------
# this stays at the bottom!

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
for mod_obj in rbuildermodels.__dict__.values():
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
for mod_obj in usersmodels.__dict__.values():
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
