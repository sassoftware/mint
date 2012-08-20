#
# Copyright (c) rPath, Inc.
#

import base64
import os
import random
import shutil
import tempfile
import urllib
import urlparse

from collections import namedtuple

from conary import dbstore
from conary.lib import util
from smartform import descriptor as smartdesc
from django.core.management import call_command
from django.db import connections, DEFAULT_DB_ALIAS
from django.test.client import Client, FakePayload
from django.test import TestCase
from django.test.simple import DjangoTestSuiteRunner
from django.utils.http import urlencode
from rmake3.core import types

from mint import config as mintconfig
from mint import buildtypes
from mint.db import schema
from mint.django_rest.rbuilder.inventory import models as invmodels
from mint.django_rest.rbuilder.inventory import zones as zmodels
from mint.django_rest.rbuilder.jobs import models as jobmodels
from mint.django_rest.rbuilder.projects import models as projmodels
from mint.django_rest.rbuilder.users import models as usermodels
from mint.django_rest.rbuilder.manager import rbuildermanager
from mint.django_rest.rbuilder.modellib import Cache

from testrunner import testcase

# XXX this import fails when running the testsuite from manage_local.
# Work around, but will need to be fixed - misa 2011-08-05
# from mint_test import mint_rephelp
MINT_PROJECT_DOMAIN = 'rpath.local2'

class TestRunner(DjangoTestSuiteRunner):

    DB_DUMP = tempfile.NamedTemporaryFile(
        prefix="mint-django-fixture-", delete=False).name

    def setup_databases(self, **kwargs):
        "Called by django's testsuite"
        return self._setupDatabases(**kwargs)

    @classmethod
    def _setupDatabases(cls, **kwargs):
        # We don't care about a lot of the complexities in
        # DjangoTestSuiteRunner
        conn = cls.getConnection()
        dbname = conn.settings_dict['TEST_NAME']
        # XXX sqlite only for now
        util.removeIfExists(dbname)
        db = dbstore.connect(dbname, 'sqlite')
        schema.loadSchema(db)
        db.commit()
        db.close()
        oldDbName = conn.settings_dict['NAME']
        conn.settings_dict['NAME'] = dbname
        # Test connection
        conn.cursor()
        cls._sqlite_dump(dbname, cls.DB_DUMP)
        return ([(conn, oldDbName, True)], [])

    @classmethod
    def _sqlite_dump(cls, srcfile, dstfile):
        util.execute("sqlite3 '%s' .dump > '%s'" % (srcfile, dstfile))

    @classmethod
    def _sqlite_restore(cls, srcfile, dstfile):
        tfile = util.AtomicFile(dstfile)
        cmd = "sqlite3 '%s' < '%s'" % (tfile.name, srcfile)
        util.execute(cmd)
        util.removeIfExists(dstfile + '.journal')
        tfile.commit()

    @classmethod
    def getConnection(cls):
        alias = DEFAULT_DB_ALIAS
        conn = connections[alias]
        return conn

    @classmethod
    def setupFixture(cls):
        s = os.stat(cls.DB_DUMP)
        if s.st_size == 0:
            # DB not set up yet
            cls._setupDatabases()
        else:
            conn = cls.getConnection()
            dbName = conn.settings_dict['TEST_NAME']
            cls._sqlite_restore(cls.DB_DUMP, dbName)
            # This will force a re-init
            conn.close()

class XMLTestCase(TestCase, testcase.MockMixIn):
    ImageFile = namedtuple('ImageFile', 'title url size sha1')

    @classmethod
    def uuid4(cls):
        from mint.lib import uuid
        return uuid.uuid4()

    def _fixture_setup(self):
        "Called by django's testsuite"
        alias = DEFAULT_DB_ALIAS
        TestRunner.setupFixture()
        # Test connection
        conn = TestRunner.getConnection()
        conn.cursor()
        call_command('loaddata', 'initial_data',
            **dict(verbosity=0, database=alias))
        if hasattr(self, 'fixtures'):
            call_command('loaddata', *self.fixtures,
                **dict(verbosity=0, database=alias))

    def _getMintConfig(self):
        connection = TestRunner.getConnection()

        cfg = mintconfig.MintConfig()
        cfg.siteHost = 'localhost.localdomain'
        cfg.dbDriver = 'sqlite'
        cfg.dbPath = connection.settings_dict['TEST_NAME']
        cfg.projectDomainName = MINT_PROJECT_DOMAIN
        cfg.namespace = 'ns'
        cfg.authUser = 'auth_user_abcdefg'
        cfg.authPass = 'auth_pass_abcdefg'
        metadataDescriptorFile = os.path.join(self.workDir, "metadataDescriptor.xml")
        file(metadataDescriptorFile, "w").write("""\
<metadataDescriptor>
  <metadata>
    <displayName>Metadata Descriptor</displayName>
    <descriptions/>
  </metadata>
  <dataFields>
    <field>
      <name>metadata.owner</name>
      <descriptions><desc>Owner</desc></descriptions>
      <type>str</type>
      <required>true</required>
      <readonly>true</readonly>
    </field>
    <field>
      <name>metadata.admin</name>
      <descriptions><desc>Admin</desc></descriptions>
      <type>str</type>
      <required>true</required>
      <readonly>true</readonly>
    </field>
  </dataFields>
</metadataDescriptor>
""")
        cfg.metadataDescriptorPath = metadataDescriptorFile
        cfg.imagesPath = os.path.join(self.workDir, 'finished-images')
        cfg.moduleHooksDir = os.path.join(self.workDir, 'module-hooks')
        return cfg

    def setUp(self):
        # django tries to be smart and not print large diffs. That's not
        # very helpful
        self.maxDiff = None
        self.workDir = tempfile.mkdtemp(dir="/tmp", prefix="rbuilder-django-")
        mintCfgPath = os.path.join(self.workDir, "mint.cfg")
        self.mintCfg = self._getMintConfig()
        self.mintCfg.writeToFile(mintCfgPath)
        mintconfig.RBUILDER_CONFIG = mintCfgPath

        self.client = Client()
        self.mgr = rbuildermanager.RbuilderManager()
        self.localZone = self.mgr.sysMgr.getLocalZone()
        from mint.django_rest.rbuilder.inventory.manager import repeatermgr
        repeatermgr.repeater_client = None

        # Default to 10 items per page in the tests
        from django.conf import settings
        settings.PER_PAGE = 10
        Cache.reset()
        return TestCase.setUp(self)

    def getUser(self, userName):
        return usermodels.User.objects.get(user_name=userName)

    def tearDown(self):
        TestCase.tearDown(self)
        self.unmock()

    def failUnlessIn(self, needle, haystack):
        self.failUnless(needle in haystack, "%s not in %s" % (needle,
            haystack))

    def assertXMLEquals(self, first, second, ignoreNodes=None):
        # NOTE: really shouldn't be blocking quite so much here, but the tests are mostly
        # concerned with use cases rather than the state of these elements.
        if ignoreNodes is None:
            ignoreNodes = ['time_created', 'time_updated', 'created_date',
                'tagged_date', 'last_available_update_refresh', 'time_enabled',
                'registration_date', 'modified_date', 'last_login_date',
                'created_by', 'modified_by', 'updated_by', 'published_by',
                'full_name', 'user_name', 'is_public', 'is_static', 'time_mirrored',
                'time_published', 'latest_survey', 'current_state', 'desired_top_level_items',
                'observed_top_level_items'
            ]

        # contend with database False (sqlite only) vs synthetic false casing
        first = first.replace("true", "True")
        first = first.replace("false", "False")
        second = second.replace("true", "True")
        second = second.replace("false", "False")

        from lxml import etree
        X = XML(orderedChildren=True, ignoreNodes=ignoreNodes)
        tree0 = X.normalize(etree.fromstring(first.strip()))
        tree1 = X.normalize(etree.fromstring(second.strip()))
        nd = X.nodediff(tree0, tree1)
        if nd:
            data0 = etree.tostring(tree0, pretty_print=True, with_tail=False)
            data1 = etree.tostring(tree1, pretty_print=True, with_tail=False)
            import difflib
            diff = '\n'.join(list(difflib.unified_diff(data1.splitlines(),
                    data0.splitlines()))[2:])
            # Set this to 1 if the diff is too complicated to read
            if 0:
                diff += "\nNode diff: %s" % (nd, )
            self.fail(diff)

    def getProject(self, shortName):
        return projmodels.Project.objects.get(short_name=shortName)

    def addProject(self, shortName, domainName='test.local2',
            namespace='ns', user=None):
        project = projmodels.Project()
        project.name = project.hostname = project.short_name = shortName
        project.namespace = namespace
        project.domain_name = domainName
        if user is not None:
            if isinstance(user, basestring):
                user = self.getUser(user)
        project = self.mgr.projectManager.addProject(project, for_user=user)
        return project

    def getProjectBranch(self, label=None):
        return projmodels.ProjectVersion.objects.get(label=label)

    def addProjectBranch(self, project, name="trunk", label="label@rpath:foo"):
        branch = projmodels.ProjectVersion(project=project, name=name,
            label=label)
        branch.save()
        return branch

    def getProjectBranchStage(self, branch=None, name=None):
        return projmodels.Stage.objects.get(project_branch=branch, name=name)

    def addProjectBranchStage(self, project=None, branch=None,
            name="Development", label="label@rpath:foo-devel"):
        if project is None:
            project = branch.project
        stage = projmodels.Stage(project=project,
            project_branch=branch, name=name, label=label)
        stage.save()

    def newSystem(self, **kwargs):
        if 'managing_zone' not in kwargs:
            kwargs['managing_zone'] = self.localZone
        return invmodels.System(**kwargs)

    def addImage(self, name, description=None,
            imageType=buildtypes.VMWARE_ESX_IMAGE,
            stage=None, files=None, baseImage=None,
            fileNameTemplate='file-name-%s.ova', seed=None):
        if stage is None:
            branch = self.getProjectBranch(label='chater-foo.eng.rpath.com@rpath:chater-foo-1')
            stage = self.getProjectBranchStage(branch=branch, name="Development")
        if files is None:
            if seed is None:
                seed = random.randint(1024, 10240)
            files = [ self.ImageFile(url=fileNameTemplate % seed,
                title='Image Title %s' % seed, size=seed, sha1="%040d" % seed) ]
        # To create deferred images, pass files=[]

        img = self.mgr.createImage(name=name, description=description,
            project_branch_stage=stage,
            _image_type=imageType, base_image=baseImage)
        self.mgr.createImageBuild(img)
        for fileUrl, fileTitle, fileSize, fileSha1 in files:
            self.mgr.createImageBuildFile(img,
                url=fileUrl,
                title=fileTitle,
                size=fileSize,
                sha1=fileSha1,
            )
        # No retagging in this function
        return img

    def _addRequestAuth(self, username=None, password=None, jobToken=None, **extra):
        if username:
            type, password = self._authHeader(username, password)
            extra[type] = password
        if jobToken:
            extra['X-rBuilder-Job-Token'] = jobToken

        return extra

    def _fixPath(self, path):
        arr = path.split('://', 1)
        if len(arr) == 2:
            return path
        if path.startswith('/'):
            return path
        return '/api/v1/' + path

    # Ugly
    def _parseRedirect(self, http_redirect, pagination=''):
        redirect_url = http_redirect['Location']
        return redirect_url.split('/api/v1/')[1].strip('/') + pagination

    def _get(self, url, username=None, password=None, pagination='', *args, **kwargs):
        """
        HTTP GET. Handles redirects & pagination.
        The pagination parameter allows us to include an offset and
        limit big enough that our test data will not be truncated.
        """
        response = self._get_internal(url, username=username, password=password)
        if str(response.status_code).startswith('3') and response.has_header('Location'):
            new_url = self._parseRedirect(response, pagination)
            response = self._get_internal(new_url, username=username, password=password)
        return response

    def _get_internal(self, path, data={}, username=None, password=None, follow=False, headers=None):
        path = self._fixPath(path)
        params = data.copy()
        parsed = urlparse.urlparse(path)
        if parsed.params:
            for param in parsed.params.split(';'):
                if param.find("=") != -1:
                    k, v = param.split('=')
                    params[k] = v

        extra = self._addRequestAuth(username, password)
        extra.update(headers or {})
        return self.client.get(path, params, follow, **extra)

    def _post(self, path, data={}, content_type='application/xml',
             username=None, password=None, follow=False, headers=None,
             jobToken=None):
        path = self._fixPath(path)
        extra = self._addRequestAuth(username, password, jobToken=jobToken)
        extra.update(headers or {})
        return self.client.post(path, data, content_type, follow, **extra)

    def _put(self, path, data={}, content_type='application/xml',
            username=None, password=None, follow=False, headers=None,
            jobToken=None):
        path = self._fixPath(path)
        extra = self._addRequestAuth(username, password, jobToken=jobToken)
        extra.update(headers or {})
        return self.client.put(path, data, content_type, follow, **extra)

    def _delete(self, path, data='', follow=False, username=None,
                password=None, headers=None, content_type='application_xml'):
        """
        Send a DELETE request to the server.
        """
        path = self._fixPath(path)
        extra = self._addRequestAuth(username, password)
        extra.update(headers or {})
        post_data = data

        query_string = None
        if not isinstance(data, basestring):
            query_string = urlencode(data, doseq=True)

        parsed = urlparse.urlparse(path)
        r = {
            'CONTENT_LENGTH': len(post_data),
            'CONTENT_TYPE':   content_type,
            'PATH_INFO':      urllib.unquote(parsed[2]),
            'QUERY_STRING':   query_string or parsed[4],
            'REQUEST_METHOD': 'DELETE',
            'wsgi.input':     FakePayload(post_data),
        }
        r.update(extra)

        response = self.client.request(**r)
        if follow:
            response = self.client._handle_redirects(response, **extra)
        return response

    def _authHeader(self, username, password):
        authStr = "%s:%s" % (username, password)
        return ("Authorization", "Basic %s" % base64.b64encode(authStr))

    def _saveZone(self, zoneName=None, zoneDescription=None):
        if zoneName is None:
            zoneName = "Local Zone"
        zones = zmodels.Zone.objects.filter(name=zoneName)
        if len(zones) > 0:
            zone = zones[0]
        else:
            zone = zmodels.Zone()
            zone.name = zoneName
        zone.description = zoneDescription or "Some local zone"
        zone.save()

        return zone

    def _saveSystem(self):
        system = invmodels.System()
        system.name = 'testsystemname'
        system.description = 'testsystemdescription'
        system.local_uuid = 'testsystemlocaluuid'
        system.generated_uuid = 'testsystemgenerateduuid'
        system._ssl_client_certificate = 'testsystemsslclientcertificate'
        system._ssl_client_key = 'testsystemsslclientkey'
        system.ssl_server_certificate = 'testsystemsslservercertificate'
        system.registered = True
        system.current_state = self.mgr.sysMgr.systemState(
            invmodels.SystemState.REGISTERED)
        system.managing_zone = self.localZone
        system.management_interface = invmodels.ManagementInterface.objects.get(pk=1)
        system.system_type = invmodels.SystemType.objects.get(pk=1)
        system.save()

        network = invmodels.Network()
        network.ip_address = '1.1.1.1'
        network.device_name = 'eth0'
        network.dns_name = 'testnetwork.example.com'
        network.netmask = '255.255.255.0'
        network.port_type = 'lan'
        network.system = system
        network.save()

        return system

    def _saveManagementNode(self, zoneName=None, idx=0):
        zone = self._saveZone(zoneName=zoneName);

        if idx == 0:
            suffix = ''
            nodeJid = "superduperjid2@rbuilder.rpath"
        else:
            suffix = ' %02d' % idx
            nodeJid = "node%02d@rbuilder.rpath" % idx
        management_node = invmodels.ManagementNode()
        management_node.zone = zone
        management_node.managing_zone = zone
        management_node.name = 'test management node' + suffix
        management_node.description = 'test management node desc' + suffix
        management_node.local_uuid = 'test management node luuid' + suffix
        management_node.generated_uuid = 'test management node guuid' + suffix
        management_node._ssl_client_certificate = 'test management node client cert' + suffix
        management_node._ssl_client_key = 'test management node client key' + suffix
        management_node.ssl_server_certificate = 'test management node server cert' + suffix
        management_node.registered = True
        management_node.current_state = self.mgr.sysMgr.systemState(
            invmodels.SystemState.REGISTERED)
        management_node.local = True
        management_node.management_interface = invmodels.ManagementInterface.objects.get(pk=1)
        management_node.type = invmodels.SystemType.objects.get(pk=2)
        management_node.node_jid = nodeJid
        management_node.save()

        network = invmodels.Network()
        network.ip_address = '2.2.2.%d' % (2 + idx)
        network.device_name = 'eth0'
        network.dns_name = 'testnetwork.example.com'
        network.netmask = '255.255.255.0'
        network.port_type = 'lan'
        network.system = management_node
        network.save()

        return management_node

    def _saveSystem2(self):
        system = invmodels.System()
        system.name = 'testsystemname2'
        system.description = 'testsystemdescription2'
        system.local_uuid = 'testsystemlocaluuid2'
        system.generated_uuid = 'testsystemgenerateduuid2'
        system._ssl_client_certificate = 'testsystemsslclientcertificate2'
        system._ssl_client_key = 'testsystemsslclientkey2'
        system.ssl_server_certificate = 'testsystemsslservercertificate2'
        system.registered = True
        system.current_state = self.mgr.sysMgr.systemState(
            invmodels.SystemState.REGISTERED)
        system.managing_zone = self.localZone
        system.save()

        network = invmodels.Network()
        network.ip_address = '2.2.2.2'
        network.device_name = 'eth0'
        network.dns_name = 'testnetwork2.example.com'
        network.netmask = '255.255.255.0'
        network.port_type = 'lan'
        network.system = system
        network.save()

        return system

    def _newJob(self, jobUuid, jobType, jobToken=None, jobState=None,
            statusCode=100, statusText=None, statusDetail=None, createdBy=None):
        eventType = self.mgr.sysMgr.eventType(jobType)
        if jobState is None:
            jobState = jobmodels.JobState.RUNNING
        jobState = self.mgr.sysMgr.jobState(jobState)
        job = jobmodels.Job(job_uuid=jobUuid,
            job_token=jobToken,
            job_type=eventType,
            created_by=createdBy,
            job_state=jobState, status_code=statusCode,
            status_text=statusText or 'Initializing',
            status_detail=statusDetail)
        job.save()
        return job

    def _newSystemJob(self, system, eventUuid, jobUuid, jobType, jobState=None,
            statusCode=100, statusText=None, statusDetail=None, createdBy=None):
        job = self._newJob(jobUuid, jobType, jobState=jobState,
            statusCode=statusCode, statusText=statusText,
            statusDetail=statusDetail, createdBy=createdBy)
        systemJob = invmodels.SystemJob(system=system, job=job,
            event_uuid=eventUuid)
        systemJob.save()
        return job

    def cleanUp(self):
        shutil.rmtree(self.workDir, ignore_errors=True)

    def disablePostCommitActions(self):
        """
        Replaces the list with something that pretends to always be empty, but
        still collects the actions
        """
        self.devNullList = self.DevNullList()
        from mint.django_rest import signals
        self.mock(signals.PostCommitActions, 'actions',
            self.devNullList)

    class DevNullList(list):
        def __nonzero__(self):
            return False

class XML(object):
    class OrderedDict(dict):
        def items(self):
            return sorted(dict.items(self))

    @classmethod
    def sortKey(cls, obj):
        return obj.tag

    def __init__(self, orderedChildren=False, ignoreNodes=None):
        self.orderedChildren = orderedChildren
        self.ignoreNodes = set(ignoreNodes or ())

    def normalize(self, node, parent=None):
        """
        This function will:
        * reorder child nodes if so requested
        * ignore some of the nodes
        * strip tail and mixed content
        """
        from lxml import etree
        attrib = self.OrderedDict(node.attrib)
        nsmap = self.OrderedDict(node.nsmap)

        if parent is None:
            nnode = etree.Element(node.tag, nsmap=nsmap, attrib=attrib)
        else:
            nnode = etree.SubElement(parent, node.tag, nsmap=nsmap, attrib=attrib)
        hasChildren = False
        for x in self._iterator(node):
            if x.tag in self.ignoreNodes:
                continue
            self.normalize(x, parent=nnode)
            hasChildren = True
        if not hasChildren:
            # We don't allow for mixed content
            nnode.text = self._strip(node.text)
        return nnode

    def _iterator(self, node):
        if self.orderedChildren:
            return sorted(node, key=self.sortKey)
        return node

    @classmethod
    def _strip(cls, data):
        if data is None:
            return None
        # Convert empty string to None
        return data.strip() or None

    @classmethod
    def nodediff(cls, node1, node2):
        """
        Return False if the nodes are identical, or some random data structure
        that is intended to be helpful otherwise.
        """
        if node1.tag != node2.tag:
            return "Different nodes"
        if node1.attrib != node2.attrib:
            return "Attributes: %s != %s" % (node1.attrib, node2.attrib)
        if node1.nsmap != node2.nsmap:
            return "Namespace maps: %s != %s" % (node1.nsmap, node2.nsmap)
        children1 = [ x for x in node1.getchildren() ]
        children2 = [ x for x in node2.getchildren() ]

        if children1 or children2:
            # Compare text in nodes that have children (mixed content).
            # We shouldn't have mixed content, but we need to be flexible.
            text1 = node1.text
            text2 = node2.text
            if text1 != text2:
                return "Node text: %s != %s" % (text1, text2)
            if len(children1) != len(children2):
                ch1set = set(x.tag for x in children1)
                ch2set = set(x.tag for x in children2)
                return "Child list: Counts %d != %d: A-B: %s; B-A: %s" % (
                    len(children1), len(children2),
                    ch1set - ch2set, ch2set - ch1set)
            for ch1, ch2 in zip(children1, children2):
                nd = cls.nodediff(ch1, ch2)
                if nd:
                    if ch1.tag == ch2.tag:
                        return ("Node %s" % ch1.tag, nd)
                    return ("Nodes %s, %s" % (ch1.tag, ch2.tag), nd)
            return False
        # No children, compare the text
        if node1.text == node2.text:
            return False
        return (node1.text, node2.text)

class CallProxy(object):
    __slots__ = []
    prefix = None
    class _CallProxy(object):
        _callList = []
        # If we set _callReturn to a lambda, it will be interpreted as a
        # class method. So fake it
        _callReturn = []
        #_callData = namedtuple("CallData", "name args kwargs retval")
        _callData = namedtuple("CallData", "name args kwargs")
        def __init__(self, name, prefix=None):
            if prefix is not None:
                self._name = "%s.%s" % (prefix, name)
            else:
                self._name = name

        def __repr__(self):
            return "<%s for  %s>" % (self.__class__.__name__, self._name)

        def __getattr__(self, name):
            return self.__class__("%s.%s" % (self._name, name))

        def __call__(self, *args, **kwargs):
            ret = self._callReturn[0](self._name, args, kwargs, self._callList)
            #self._callList.append(self._callData(self._name, args, kwargs, ret))
            self._callList.append(self._callData(self._name, args, kwargs))
            return ret

    def __getattr__(self, name):
        return self._CallProxy(name, prefix=self.prefix)

    def reset(self):
        del self._CallProxy._callList[:]

    def setCallReturn(self, func):
        self._CallProxy._callReturn = [func]

    def getCallList(self):
        return self._CallProxy._callList[:]

class _StorageObject(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def __eq__(self, other):
        return self.__dict__ == other.__dict__
    def __repr__(self):
        return repr(self.__dict__)
    def pop(self, field):
        return self.__dict__.pop(field)

class _SlotStorageObject(object):
    __slots__ = []
    def __init__(self, *args, **kwargs):
        for slotName, slotVal in zip(self.__slots__, args):
            setattr(self, slotName, slotVal)
        for slotName in self.__slots__:
            if slotName in kwargs:
                setattr(self, slotName, kwargs[slotName])

class Targets(CallProxy):
    prefix = 'targets'
    class TargetConfiguration(_SlotStorageObject):
        __slots__ = ['targetType', 'targetName', 'alias', 'config',]
    class TargetUserCredentials(_SlotStorageObject):
        __slots__ = ['rbUser', 'rbUserId', 'isAdmin', 'credentials', ]

class RepeaterClient(CallProxy):
    class CimParams(_StorageObject):
        pass
    class WmiParams(CimParams):
        pass
    class ManagementInterfaceParams(CimParams):
        pass

    class ResultsLocation(_StorageObject):
        pass

    targets = Targets()

    def getJob(self, uuid):
        job = RmakeJob(uuid, 200, "status text", "status detail", True)
        # XXX FIXME: rpath-repeater has a problem serializing stuff, the
        # inner object is not freezable
        job.data.data = self._jobData
        return job

    def setJobData(self, jobData):
        self._jobData = types.FrozenObject.fromObject(jobData)

class RmakeJob(object):
    Status = namedtuple("Status", "code text detail final failed")
    class _RmakeJobData(object):
        class _Inner(object):
            def __init__(self, data):
                self.data = data
        def __init__(self, data):
            self.data = self._Inner(data)

        def getObject(self):
            return self.data

    def __init__(self, uuid, statusCode, statusText, statusDetail, final,
            failed=False):
        self.job_uuid = uuid
        self.data = self._RmakeJobData(dict(authToken='auth-token-'+uuid))
        self.status = self.Status(statusCode, statusText, statusDetail, final,
            failed)

def makeRepeaterData(serial):
    uuid = "uuid%03d" % serial
    return uuid, RmakeJob(uuid, 200, "status text", "status detail", False)

class SmartformMixIn(object):
    def setUpSchemaDir(self):
        self.schemaDir = ""
        schemaFile = "descriptor-%s.xsd" % smartdesc.BaseDescriptor.version
        schemaDir = os.path.join(os.path.dirname(os.path.realpath(
            os.path.abspath(os.path.dirname(smartdesc.__file__)))), 'xsd')
        if not os.path.exists(os.path.join(schemaDir, schemaFile)):
            # Not running from a checkout
            schemaDir = smartdesc._BaseClass.schemaDir
            assert(os.path.exists(os.path.join(schemaDir, schemaFile)))
        self.schemaDir = schemaDir
        self.mock(smartdesc.BaseDescriptor, 'schemaDir', schemaDir)
        self.mock(smartdesc.DescriptorData, 'schemaDir', schemaDir)

class RepeaterMixIn(SmartformMixIn):
    RmakeJobFactory = RmakeJob
    class RepeaterMgr(object):
        repeaterClient = RepeaterClient()
        repeaterClient.setCallReturn(
                lambda n, args, kwargs, callList: makeRepeaterData(len(callList)))

    def setUpRepeaterClient(self):
        self.setUpSchemaDir()
        self.mgr.repeaterMgr = self.RepeaterMgr()
        self.mgr.repeaterMgr.repeaterClient.reset()
        # We need to play this lambda trick so we can capture the job and pass
        # it to mockGetRmakeJob
        self.mock(jobmodels.Job, 'getRmakeJob',
            lambda slf: self.mockGetRmakeJob(slf))

        from mint.django_rest.rbuilder.inventory.manager import repeatermgr
        self.mock(repeatermgr.RepeaterManager, 'repeaterClient',
            self.mgr.repeaterMgr.repeaterClient)

    def mockGetRmakeJob(self, slf, *args, **kwargs):
        return self.RmakeJobFactory(slf.job_uuid, 200, "Mocked - all good",
            "Mocked - status detail", False)
