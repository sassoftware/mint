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
import uuid

from testutils import sqlharness

from collections import namedtuple

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

class Database(sqlharness.RepositoryDatabase):
    def createSchema(self):
        db = self.connect()
        schema.loadSchema(db)
        db.commit()

class SQLHarness(sqlharness.PostgreSQLServer):
    pass


class TestRunner(DjangoTestSuiteRunner):
    HARNESS_BINDIR = '/opt/postgresql-9.2/bin'
    HARNESS_DB = None
    FIXTURE_PATH = None

    @classmethod
    def setup_databases(cls, *args, **kwargs):
        "Called by django's testsuite"
        # We don't care about a lot of the complexities in
        # DjangoTestSuiteRunner
        return cls._setupDatabases(**kwargs)

    def teardown_databases(self, *args, **kwargs):
        if not self.HARNESS_DB:
            return
        self.HARNESS_DB.stop()
        self.__class__.HARNESS_DB = None

    @classmethod
    def _setupDatabases(cls, **kwargs):
        conn = cls.getConnection()
        oldDbName = conn.settings_dict['NAME']
        if cls.HARNESS_DB is None:
            if cls.HARNESS_BINDIR not in os.environ['PATH']:
                os.environ['PATH'] = '%s:%s' % (
                        cls.HARNESS_BINDIR, os.environ['PATH'])
            harness = SQLHarness(path=None, dbClass=Database)
            conn.settings_dict['USER'] = harness.user
            conn.settings_dict['PORT'] = harness.port
            db = harness.createDB(conn.settings_dict['TEST_NAME'])
            db.createSchema()
            cls.HARNESS_DB = db
            cls.FIXTURE_PATH = os.path.join(cls.HARNESS_DB.harness.path, "fixture")
            cls.HARNESS_DB.dumpSchema(cls.FIXTURE_PATH)
        # Test connection
        conn.cursor()
        return ([(conn, oldDbName, True)], [])

    @classmethod
    def getConnection(cls):
        alias = DEFAULT_DB_ALIAS
        conn = connections[alias]
        return conn

    @classmethod
    def setupFixture(cls):
        if cls.HARNESS_DB is None:
            # Invoked through rbuilder's test runner
            cls.setup_databases()
        cls.HARNESS_DB.clearSchema()
        cls.HARNESS_DB.loadSchemaDump(cls.FIXTURE_PATH)

    @classmethod
    def teardownFixture(cls):
        pass

class XMLTestCase(TestCase, testcase.MockMixIn):
    ImageFile = namedtuple('ImageFile', 'title url size sha1')

    @classmethod
    def uuid4(cls):
        return uuid.uuid4()

    def _fixture_setup(self):
        "Called by django's testsuite"
        alias = DEFAULT_DB_ALIAS
        TestRunner.setupFixture()
        if not hasattr(self, 'fixtures'):
            self.fixtures = []
        self.fixtures.insert(0, 'initial_data')
        # We use only one db, and we don't need to flush it
        call_command('loaddata', *self.fixtures,
                **dict(verbosity=0, database=alias))

    def _fixture_setupP2(self):
        "Called by django's testsuite"
        alias = DEFAULT_DB_ALIAS
        TestRunner.setupFixture()
        # We use only one db, and we don't need to flush it
        call_command('loaddata', 'initial_data',
                **dict(verbosity=0, database=alias))
        if hasattr(self, 'fixtures'):
            call_command('loaddata', *self.fixtures,
                    **dict(verbosity=0, database=alias))

    def _fixture_setupP1(self):
        TestRunner.setupFixture()
        origFixtures = None
        if hasattr(self, 'fixtures'):
            origFixtures = self.fixtures
        self.fixtures = [ 'initial_data' ]
        TestCase._fixture_setup(self)
        if origFixtures is not None:
            self.fixtures = origFixtures
            TestCase._fixture_setup(self)
        else:
            del self.fixtures

    def _fixture_setupP(self):
        TestRunner.setupFixture()
        if not hasattr(self, 'fixtures'):
            self.fixtures = []
        if self.fixtures[0] != 'initial_data':
            self.fixtures.insert(0, 'initial_data')
        TestCase._fixture_setup(self)

    def _fixture_teardown(self):
        TestCase._fixture_teardown(self)
        TestRunner.teardownFixture()

    def _getMintConfig(self):
        connection = TestRunner.getConnection()

        cfg = mintconfig.MintConfig()
        cfg.siteHost = 'localhost.localdomain'
        cfg.dbDriver = 'postgresql'
        _d = connection.settings_dict
        cfg.dbPath = "%s@%s:%s/%s" % (_d['USER'], _d['HOST'], _d['PORT'],
                _d['TEST_NAME'])
        cfg.projectDomainName = MINT_PROJECT_DOMAIN
        cfg.namespace = 'ns'
        cfg.authUser = 'auth_user_abcdefg'
        cfg.authPass = 'auth_pass_abcdefg'
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
                'time_published', 'current_state',
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

    def assertRaises(self, excClass, callableObj=None, *args, **kwargs):
        # Override so that the exception is returned. But also try to pass
        # through the context manager feature added in Python 2.7
        if callableObj is None:
            return super(XMLTestCase, self)(excClass, callableObj,
                    *args, **kwargs)
        try:
            callableObj(*args, **kwargs)
        except excClass, err:
            return err
        else:
            try:
                exc_name = excClass.__name__
            except AttributeError:
                exc_name = str(excClass)
            raise self.failureException("%s not raised" % exc_name)
    failUnlessRaises = assertRaises

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
            stage=None, files=None,
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
            _image_type=imageType)
        if not img.architecture and not img.trove_flavor:
            img.trove_flavor = ''
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
        extra['mint.authToken'] = (username, password)
        extra['mint.wsgiContext'] = namedtuple('fakecontext', 'cfg db')(
                cfg=self.mintCfg,
                db=None,
                )
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

    def _get(self, url, username=None, password=None, pagination='',
            headers=None, *args, **kwargs):
        """
        HTTP GET. Handles redirects & pagination.
        The pagination parameter allows us to include an offset and
        limit big enough that our test data will not be truncated.
        """
        response = self._get_internal(url, username=username, password=password,
                headers=headers)
        if str(response.status_code).startswith('3') and response.has_header('Location'):
            new_url = self._parseRedirect(response, pagination)
            response = self._get_internal(new_url, username=username,
                    password=password, headers=headers)
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
             jobToken=None, zone=None):
        path = self._fixPath(path)
        extra = self._addRequestAuth(username, password, jobToken=jobToken)
        extra.update(headers or {})
        if zone is not None:
            extra['X-rPath-Management-Zone'] = base64.b64encode(zone.name)
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

    def __init__(self):
        self.reset()

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
        vals = {}
        for slotName, slotVal in zip(self.__slots__, args):
            vals[slotName] = slotVal
        for slotName in self.__slots__:
            setattr(self, slotName, kwargs.get(slotName, vals.get(slotName)))

class Targets(CallProxy):
    prefix = 'targets'
    class TargetConfiguration(_SlotStorageObject):
        __slots__ = ['targetType', 'targetName', 'alias', 'config',]
    class TargetUserCredentials(_SlotStorageObject):
        __slots__ = ['rbUser', 'rbUserId', 'isAdmin', 'credentials', ]

class RepeaterClient(_SlotStorageObject, CallProxy):
    __slots__ = [ '_jobData', '_jobStatusCode', '_jobStatusText',
        '_jobStatusDetail', '_jobStatusFinal', '_jobStatusFailed', ]
    class CimParams(_StorageObject):
        pass
    class WmiParams(CimParams):
        pass
    class ManagementInterfaceParams(CimParams):
        pass

    class ResultsLocation(_StorageObject):
        pass

    targets = Targets()

    def __init__(self):
        _SlotStorageObject.__init__(self)
        CallProxy.__init__(self)

    def reset(self):
        # Restore all the slot values to None
        _SlotStorageObject.__init__(self)
        CallProxy.reset(self)

    def getJob(self, uuid):
        statusCode = self._jobStatusCode or 200
        statusText = self._jobStatusText or "status text"
        statusDetail = self._jobStatusDetail or "status detail"
        final = self._jobStatusFinal or True
        failed = self._jobStatusFailed or False
        job = RmakeJob(uuid, statusCode, statusText, statusDetail, final,
                failed)
        # XXX FIXME: rpath-repeater has a problem serializing stuff, the
        # inner object is not freezable
        job.data = self._jobData
        return job

    def setJobData(self, jobData=None, status=None, text=None, detail=None,
            final=None, failed=None):
        if jobData is not None:
            self._jobData = types.FrozenObject.fromObject(jobData)
        if status is not None:
            self._jobStatusCode = status
        if text is not None:
            self._jobStatusText = text
        if detail is not None:
            self._jobStatusDetail = detail
        if final is not None:
            self._jobStatusFinal = final
        if failed is not None:
            self._jobStatusFailed = failed

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

def makeRepeaterData(n, args, kwargs, callList):
    uuid = kwargs.get('uuid', "uuid%03d" % len(callList))
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
                lambda n, args, kwargs, callList: makeRepeaterData(n, args, kwargs, callList))

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
