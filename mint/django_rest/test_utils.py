#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import base64
import os
import shutil
import tempfile
import urllib
import urlparse

from conary import dbstore
from conary.lib import util
from django.core.management import call_command
from django.db import connections, DEFAULT_DB_ALIAS
from django.test.client import Client, FakePayload
from django.test import TestCase
from django.test.simple import DjangoTestSuiteRunner
from django.utils.http import urlencode

from mint import config as mintconfig
from mint.db import schema
from mint.django_rest.rbuilder.inventory import models as invmodels
from mint.django_rest.rbuilder.inventory import views
from mint.django_rest.rbuilder.jobs import models as jobmodels
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager import rbuildermanager

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
        from mint.db import database
        # Turn off temporary table creation, because django keeps the db locked
        database.Database._createTemporaryTables = lambda *args, **kwargs: None
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
        return cfg

    def setUp(self):
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
        return TestCase.setUp(self)

    def tearDown(self):
        TestCase.tearDown(self)
        self.unmock()

    def failUnlessIn(self, needle, haystack):
        self.failUnless(needle in haystack, "%s not in %s" % (needle,
            haystack))

    def assertXMLEquals(self, first, second, ignoreNodes=None):
        if ignoreNodes is None:
            ignoreNodes = ['time_created', 'time_updated', 'created_date',
                'last_available_update_refresh', 'time_enabled',
                'registration_date', 'modified_date']
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

    def newSystem(self, **kwargs):
        if 'managing_zone' not in kwargs:
            kwargs['managing_zone'] = self.localZone
        return invmodels.System(**kwargs)

    def _addRequestAuth(self, username=None, password=None, **extra):
        if username:
            type, password = self._authHeader(username, password)
            extra[type] = password

        return extra

    def _fixPath(self, path):
        arr = path.split('://', 1)
        if len(arr) == 2:
            return path
        if path.startswith('/'):
            return path
        return '/api/v1/' + path

    def _get(self, path, data={}, username=None, password=None, follow=False, headers=None):
        path = self._fixPath(path)
        params = data.copy()
        parsed = urlparse.urlparse(path)
        if parsed.params:
            for param in parsed.params.split(';'):
                k, v = param.split('=')
                params[k] = v

        extra = self._addRequestAuth(username, password)
        extra.update(headers or {})
        return self.client.get(path, params, follow, **extra)

    def _post(self, path, data={}, content_type='application/xml',
             username=None, password=None, follow=False, headers=None):
        path = self._fixPath(path)
        extra = self._addRequestAuth(username, password)
        extra.update(headers or {})
        return self.client.post(path, data, content_type, follow, **extra)

    def _put(self, path, data={}, content_type='application/xml',
            username=None, password=None, follow=False, headers=None):
        path = self._fixPath(path)
        extra = self._addRequestAuth(username, password)
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
        zones = invmodels.Zone.objects.filter(name=zoneName)
        if len(zones) > 0:
            zone = zones[0]
        else:
            zone = invmodels.Zone()
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
        system.ssl_client_certificate = 'testsystemsslclientcertificate'
        system.ssl_client_key = 'testsystemsslclientkey'
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
        management_node.ssl_client_certificate = 'test management node client cert' + suffix
        management_node.ssl_client_key = 'test management node client key' + suffix
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
        system.ssl_client_certificate = 'testsystemsslclientcertificate2'
        system.ssl_client_key = 'testsystemsslclientkey2'
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

    def _newJob(self, system, eventUuid, jobUuid, jobType, jobState=None,
            statusCode=100, statusText=None, statusDetail=None):
        eventType = self.mgr.sysMgr.eventType(jobType)
        if jobState is None:
            jobState = jobmodels.JobState.RUNNING
        jobState = self.mgr.sysMgr.jobState(jobState)
        job = jobmodels.Job(job_uuid=jobUuid, job_type=eventType,
            job_state=jobState, status_code=statusCode,
            status_text=statusText or 'Initializing',
            status_detail=statusDetail)
        job.save()
        systemJob = invmodels.SystemJob(system=system, job=job,
            event_uuid=eventUuid)
        systemJob.save()
        return job

    def cleanUp(self):
        shutil.rmtree(self.workDir, ignore_errors=True)

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