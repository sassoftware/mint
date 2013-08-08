#
# Copyright (c) 2011 rPath, Inc.
#

import re
import sys
from django.db import models
from mint import projects as mintprojects
from mint import helperfuncs, userlevels
from mint.django_rest.rbuilder import modellib
from mint.django_rest.deco import D
from mint.django_rest.rbuilder.users import models as usermodels
# avoid circular reference:
#from mint.django_rest.rbuilder.querysets import models as querymodels
from xobj import xobj

class Groups(modellib.XObjModel):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(tag='groups')

    list_fields = ['group']


class Group(modellib.XObjIdModel):
    class Meta:
        abstract = True

    # tag name is only groups for the sake of calculating project_branch_stage(s)
    # once Group(s) is moved over, change back to singular
    _xobj = xobj.XObjMetadata(tag='groups', attributes={'href':str, 'promote_href':str})

    href = models.CharField(max_length=1026)
    promote_href = models.CharField(max_length=1026)
    # group_id = models.AutoField(primary_key=True)
    # hostname = models.CharField(max_length=1026)
    # name = models.CharField(max_length=1026)
    # version = models.CharField(max_length=1026)
    # label = models.CharField(max_length=1026)
    # trailing = models.CharField(max_length=1026)
    # flavor = models.TextField()
    # time_stamp = models.DecimalField()
    # images = modellib.DeferredForeignKey('Image')
    # image_count = models.IntegerField()

    def __init__(self, href=None, promote_href=None, *args, **kwargs):
        if href:
            self.href = href
        if promote_href:
            self.promote_href = promote_href


class Projects(modellib.Collection):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                tag = "projects")
    view_name = "Projects"
    list_fields = ["project"]
    project = []

class Project(modellib.XObjIdModel):
    class Meta:
        db_table = u"projects"

    _xobj = xobj.XObjMetadata(tag='project')
    _xobj_hidden_accessors = set(['membership', 'package_set',
        'platform_set', 'productplatform_set', 'tags', 'project_tags', 'abstractplatform_set', 'labels'])
    _queryset_resource_type = 'project'
    view_name = "Project"
    url_key = ["short_name"]
    summary_view = ["name", "short_name", "domain_name"]

    project_id = models.AutoField(primary_key=True, db_column="projectid",
        blank=True)
    hostname = D(models.CharField(unique=True, max_length=63),
        "Project hostname, must be unique", short="Project hostname")
    name = D(models.CharField(unique=True, max_length=128),
        "Project name, must be unique", short="Project name")
    namespace = D(models.CharField(max_length=16, null=True),
        "Project namespace, defaults to null", short="Project namespace")
    domain_name = D(models.CharField(max_length=128, db_column="domainname"),
        "Project domain name", short="Project domain name")
    short_name = D(models.CharField(unique=True, max_length=63, db_column="shortname"),
        "Project short name, must be unique", short="Project short name")
    project_url = D(models.CharField(max_length=128, blank=True, db_column= "projecturl"),
        "Project URL, is blank by default", short="Project URL")
    repository_hostname = D(models.CharField(max_length=255, db_column="fqdn"),
        "Project repository hostname", short="Project repository hostname")
    description = D(models.TextField(null=True, blank=True),
        "Project description, null and blank by default", short="Project description")
    project_type = D(models.CharField(max_length=128, db_column="prodtype", default="Appliance"),
        "Project type, defaults to 'Appliance'", short="Project type")
    commit_email = D(models.CharField(max_length=128, null=True, blank=True, db_column="commitemail"),
        "Project commit email, defaults to null and blank", short="Project commit email")
    backup_external = D(models.BooleanField(default=False, db_column="backupexternal"),
        "Boolean, defaults to False")
    created_date = D(modellib.DecimalTimestampField(
        blank=True, db_column="timecreated"), "Project created date, is blank by default", short="Project created date")
    modified_date = D(modellib.DecimalTimestampField(
        blank=True, db_column="timemodified"), "Project modified date, is blank by default", short="Project modified date")
    hidden = D(models.BooleanField(default=False), 'Boolean, defaults to False')
    created_by = D(models.ForeignKey(usermodels.User,
        related_name="+", null=True, db_column="creatorid"), "Project creator, null by default", short="Project creator")
    external = D(models.BooleanField(default=False),
        "Is the project external?  Boolean, defaults to False", short="Project external?")
    disabled = D(models.BooleanField(default=False),
        "Is the project disabled? Boolean, defaults to False", short="Project disabled?")
    is_appliance = D(models.BooleanField(default=True, db_column="isappliance"), 'Boolean, defaults to False')
    version = D(models.CharField(max_length=128, null=True, blank=True,
        default=''), "Project version, is blank and null by default", short="Project version")
    database = D(models.CharField(max_length=128, null=True), "Project database, is null by default", short="Project database")
    members = D(modellib.DeferredManyToManyField(usermodels.User,
        through="Member"), 'User member')
    modified_by = D(models.ForeignKey(usermodels.User, null=True, related_name='+', db_column="modified_by"),
        "Project modified by, defaults to null", short="Project modified by")

    # synthetic properties hoisted from labels - these will eventually be merged
    # into the projects schema instead of a labels table
    upstream_url = D(modellib.SyntheticField(), "Project upstream URL", short="Project upstream URL")
    auth_type = D(modellib.SyntheticField(), "Project auth type", short="Project auth type")
    user_name = D(modellib.SyntheticField(), "Project user name", short="Project user name")
    password = D(modellib.SyntheticField(), "Project password", short="Project password")
    entitlement = D(modellib.SyntheticField(), "Project entitlement", short="Project entitlement")
    actions = modellib.SyntheticField()
    repository_api = D(modellib.SyntheticField(modellib.HrefField()), "Project repository API URL", short="Project repo API URL")

    load_fields = [ short_name ]

    _ApplianceTypes = set([ "Appliance", "PlatformFoundation", ])

    RESERVED_HOSTS = ['admin', 'mail', 'mint', 'www', 'web', 'rpath', 'wiki', 'lists']

    def __unicode__(self):
        return self.hostname

    def computeSyntheticFields(self, sender, **kwargs):
        self._computeRepositoryAPI()
        # Attach URL and auth data from Labels if and only if this is a
        # proxy-mode external project. Otherwise these fields are meaningless.
        if not self.database:
            labels = self.labels.all()
            if labels:
                label = labels[0]
                self.upstream_url = label.url
                self.auth_type = label.auth_type
                self.user_name = label.user_name
                self.password = label.password
                self.entitlement = label.entitlement

    def serialize(self, request=None, **kwargs):
        etreeModel = modellib.XObjIdModel.serialize(self, request, **kwargs)
        if request is not None:
            member = self.membership.filter(user=request._authUser)
            if member:
                role = userlevels.names[member[0].level]
                modellib.Etree.Node('role', parent=etreeModel, text=role)

        return etreeModel

    def _computeRepositoryAPI(self):
        self.repository_api = modellib.HrefField(
            href='/repos/%s/api' % self.short_name,
        )

    def setIsAppliance(self):
        self.is_appliance = (self.project_type in self._ApplianceTypes)

    @classmethod
    def validateNamespace(cls, namespace):
        return mintprojects._validateNamespace(namespace)

    def save(self, *args, **kwargs):
        # FIXME: move code into mgr.addProject

        if self._rbmgr is not None:
            cfg = self._rbmgr.cfg
        else:
            cfg = None
        if self.domain_name is None and cfg:
            self.domain_name = cfg.projectDomainName
        if self.namespace is None and cfg:
            self.namespace = cfg.namespace
        if not self.hostname:
            self.hostname = self.short_name

        self.validateNamespace(self.namespace)
        mintprojects._validateShortname(self.short_name, self.domain_name,
            self.RESERVED_HOSTS)
        mintprojects._validateHostname(self.hostname, self.domain_name,
            self.RESERVED_HOSTS)

        # Default project type to Appliance
        if self.project_type is None:
            self.project_type = "Appliance"
        if not self.project_url:
            self.project_url = ''

        self.setIsAppliance()

        if not self.repository_hostname and self.hostname and self.domain_name:
            self.repository_hostname = '%s.%s' % (self.hostname, self.domain_name)

        labels = self.labels.all()
        if labels:
            label = labels[0]
            if self.database:
                # Internal projects and mirror projects have no use for these
                # fields so make sure they are nulled out.
                label.url = None
                label.auth_type = 'none'
                label.user_name = None
                label.password = None
                label.entitlement = None
            else:
                assert self.external
                label.url = str(self.upstream_url)
                label.auth_type = str(self.auth_type)
                label.user_name = str(self.user_name)
                label.password = str(self.password)
                label.entitlement = str(self.entitlement)
            # This field doesn't mean anything but some old code might still
            # use it.
            label.label = self.repository_hostname + '@dummy:label'
            label.save()
        return modellib.XObjIdModel.save(self, *args, **kwargs)

class Members(modellib.Collection):
    class Meta:
        abstract = True

    list_fields = ["member"]
    member = []
    view_name = "ProjectMembers"

class Member(modellib.XObjModel):
    project = D(models.ForeignKey(Project, db_column='projectid',
        related_name='membership', primary_key=True), 'Project member')
    user = D(modellib.DeferredForeignKey(usermodels.User, db_column='userid',
        related_name='project_membership'), 'User with membership')
    level = D(models.SmallIntegerField(), 'User level, is integer')
    class Meta:
        db_table = u'projectusers'

class ProjectVersions(modellib.Collection):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                tag = "project_branches")
    view_name = "ProjectVersions"
    list_fields = ["project_branch"]
    version = []

class ProjectVersion(modellib.XObjIdModel):
    # a.k.a. "branch"
    class Meta:
        db_table = u'productversions'

    _xobj = xobj.XObjMetadata(
        tag="project_branch")
    _xobj_hidden_accessors = set(['images', 'systems', ])

    view_name = 'ProjectVersion'
    summary_view = ["name"]

    branch_id = D(models.AutoField(primary_key=True,
        db_column='productversionid'), "Branch ID", short="Project Branch ID")
    project = D(modellib.DeferredForeignKey(Project, db_column='projectid',
        related_name="project_branches", view_name="ProjectVersions"), 'Project attached to the project branch')
    label = D(models.TextField(unique=True, null=False),
        "Branch label, cannot be null and must be unique", short="Branch label")
    source_group = D(models.TextField(null=True),
        "Branch source group, defaults to null", short="Branch source group")
    cache_key = modellib.XObjHidden(models.TextField(null=True))
    namespace = D(models.CharField(max_length=16), "Branch namespace", short="Branch namespace")
    name = D(models.CharField(max_length=16), "Branch name", short="Branch name")
    description = D(models.TextField(), "Branch description", short="Branch description")
    platform_label = D(models.TextField(null=True),
        "Branch platform label, defaults to null", short="Branch platform label")
    build_standard_group = D(models.BooleanField(default=False),
        "Build standard group? Boolean, defaults to False",
        short="Build standard group?")
    created_date = D(modellib.DecimalTimestampField(
        db_column="timecreated"), "Branch created date", short="Branch created date")
    modified_date = D(modellib.DecimalTimestampField(
        db_column="timemodified"), "Branch modified date", short="Branch modified date")

    platform_id = modellib.XObjHidden(models.IntegerField(null=True, db_column='platform_id'))
    created_by = D(modellib.DeferredForeignKey(usermodels.User, db_column='created_by', null=True,
        related_name='+'), "Branch creator")
    modified_by = D(modellib.DeferredForeignKey(usermodels.User, db_column='modified_by', null=True,
        related_name='+'), "Branch last modified by")


    images = modellib.SyntheticField()
    definition = modellib.SyntheticField(modellib.HrefField())
# FIXME: This should be a FK rather than a ref to the old platform API once
#        the new platform api is in use.
#    platform = models.ForeignKey('platforms.Platform', null=True,
#        related_name='branches')

    platform = D(modellib.SyntheticField(modellib.HrefField()), "Project Branch platform", short="Project Branch platform")
    platform_version = D(modellib.SyntheticField(modellib.HrefField()), "Project Branch platform version", short="Project Branch platform version")
    imageDefinitions = modellib.SyntheticField(modellib.HrefField()) # only camelCase for compatibility reasons, CHANGE
    image_type_definitions = modellib.SyntheticField(modellib.HrefField())
    repository_api = modellib.SyntheticField(modellib.HrefField())

    def __unicode__(self):
        return self.name

    def computeSyntheticFields(self, sender, **kwargs):
        self._computePlatform()
        self._computePlatformVersion()

    def _computePlatform(self):
        if self.platform_id is None:
            return

        self.platform = modellib.HrefField(
            href='/api/platforms/%s' % self.platform_id,
        )

    def _computeRepositoryAPI(self):
        self.repository_api = modellib.HrefField(
            href='/repos/%s/api' % self.project.short_name,
        )

    def _computePlatformVersion(self):
        if self.platform_id is None:
            return

        self.platform_version = modellib.HrefField(
            href='/api/products/%s/versions/%s/platformVersion'
                % (self.project.short_name, self.name),
        )

    def save(self, *args, **kwargs):
        prodDef = self._getSanitizedProductDefinition()
        if self.label is None:
            self.label = prodDef.getProductDefinitionLabel()
        self.validate()
        return modellib.XObjIdModel.save(self, *args, **kwargs)

    def _getSanitizedProductDefinition(self):
        project = self.project
        if not self.namespace:
            self.namespace = project.namespace
        Project.validateNamespace(self.namespace)
        prodDef = helperfuncs.sanitizeProductDefinition(
            project.name, project.description, project.repository_hostname,
            project.short_name, self.name, self.description, self.namespace)
        return prodDef

    def get_url_key(self, *args, **kwargs):
        return [ self.project.short_name, self.label ]

    def serialize(self, request=None, **kwargs):
#        if request is not None:
#            self._computeRepositoryAPI()

        oldUrlValues = (self.project.short_name, self.name)
        self.imageDefinitions = modellib.HrefField(
            href='/api/products/%s/versions/%s/imageDefinitions',
            values=oldUrlValues)
        self.image_type_definitions = modellib.HrefField(
            href='/api/products/%s/versions/%s/imageTypeDefinitions',
            values=oldUrlValues)
        self.definition = modellib.HrefField(
            href='/api/products/%s/versions/%s/definition',
            values=oldUrlValues)
        etreeModel = modellib.XObjIdModel.serialize(self, request, **kwargs)
        return etreeModel

    @classmethod
    def validateProjectBranchName(cls, versionName):
        validProjectVersion = re.compile('^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*$')
        if not versionName:
            raise mintprojects.ProductVersionInvalid
        if not validProjectVersion.match(versionName):
            raise mintprojects.ProductVersionInvalid
        return None

    def validate(self):
        if self.label.split('@')[0].lower() != (self.project.repository_hostname.lower()):
            raise mintprojects.InvalidLabel(self.label)


class Stages(modellib.Collection):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                tag = "project_branch_stages")
    view_name = "ProjectBranchStages"
    list_fields = ["project_branch_stage"]

    def get_url_key(self, *args, **kwargs):
        return getattr(self, '_url_key', [])

class Stage(modellib.XObjIdModel):
    class Meta:
        db_table = 'project_branch_stage'

    view_name = 'ProjectBranchStage'
    _xobj = xobj.XObjMetadata(tag='project_branch_stage')
    _xobj_hidden_accessors = set(['version_set', 'tags', 'build_set'])

    summary_view = ["name"]

    stage_id = D(models.AutoField(primary_key=True), "Stage id", short="Project Stage id")
    project = D(modellib.DeferredForeignKey(Project,
        related_name="project_branch_stages",
        related_view_name="ProjectBranchesAllStages"), "Project for the stage")
    project_branch = D(modellib.DeferredForeignKey(ProjectVersion,
        related_name="project_branch_stages",
        related_view_name="ProjectBranchStages"),
        'Project branch for the stage')
    name = D(models.CharField(max_length=256), "Stage name", short="Stage name")
    label = D(models.TextField(null=False), "Stage label, cannot be null", short="Stage label")
    promotable = D(models.BooleanField(default=False),
        "Stage promotable? Boolean, defaults to False", short="Stage promotable?")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True), "Stage created date", short="Stage created date")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True), "Stage modified date", short="Stage modified date")
    created_by = D(models.ForeignKey(usermodels.User, related_name="+", null=True, db_column="created_by"), "Stage creator", short="Stage creator")
    modified_by = D(models.ForeignKey(usermodels.User, related_name="+", null=True, db_column="modified_by"), "Stage modifier", short="Stage modifier")
    external = modellib.SyntheticField(models.BooleanField())
    groups = modellib.SyntheticField()
    repository_api = modellib.SyntheticField(modellib.HrefField())

    def get_url_key(self, *args, **kwargs):
        return [ self.project.short_name, self.project_branch.label, self.name ]

    def computeSyntheticFields(self, sender, **kwargs):
        ''' Compute non-database fields.'''
        if self.project_id is None:
            self.external = False
        else:
            self.external = self.project.external

    def _computeRepositoryAPI(self):
        self.repository_api = modellib.HrefField(
            href='/repos/%s/api' % self.project.short_name,
        )

    def serialize(self, request=None, **kwargs):
        if request:
            self._computeRepositoryAPI()
            product = ('https://' + request.get_host().strip('/') +
                '/api/products/%s')

            href = product + '/repos/search?type=group&label=%s'
            short_name = self.project.short_name
            label = self.label

            # FIXME: This should be moved into a job later.
            promote_href = product + '/versions/%s/stages/%s'

            self.groups = Group(
                href=href % (short_name, label),
                promote_href=promote_href
                    % (short_name, self.project_branch.name, self.name))
        etreeModel = modellib.XObjIdModel.serialize(self, request, **kwargs)
        return etreeModel

class InboundMirror(modellib.XObjModel):
    _xobj = xobj.XObjMetadata(tag="inbound_mirror")
    class Meta:
        db_table = "inboundmirrors"

    inbound_mirror_id = models.AutoField(primary_key=True,
        db_column="inboundmirrorid")
    target_project = modellib.ForeignKey(Project,
        related_name="inbound_mirrors",
        db_column="targetprojectid")
    source_labels = models.CharField(max_length=767,
        db_column="sourcelabels")
    source_url = models.CharField(max_length=767,
        db_column="sourceurl")
    source_auth_type = models.CharField(max_length=32,
        db_column="sourceauthtype")
    source_user_name = models.CharField(max_length=254, null=True,
        db_column="sourceusername")
    source_password = models.CharField(max_length=254, null=True,
        db_column="sourcepassword")
    source_entitlement = models.CharField(max_length=254, null=True,
        db_column="sourceentitlement")
    mirror_order = models.IntegerField(default=0, null=True,
        db_column="mirrororder")
    all_labels = models.IntegerField(default=0, null=True,
        db_column="alllabels")

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj
