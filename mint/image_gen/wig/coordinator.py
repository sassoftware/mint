#
# Copyright (c) 2010 rPath, Inc.
#
# All rights reserved.
#

import random
from twisted.internet import defer as tw_defer
from twisted.internet import protocol as tw_proto
from twisted.web import client as tw_web_client
from xobj import xobj


class Coordinator(object):
    """
    Maintain a list of rPath Windows Build Service nodes and assign image build
    jobs to nodes as appropriate.
    """

    def __init__(self, reactor, hostname):
        self.reactor = reactor
        self.hostname = hostname
        self.services = []

    def listSystems(self):
        """Collect a list of rPath Windows Build Services from inventory."""
        url = 'http://%s/api/inventory/' % (self.hostname,)
        # Get list of system types so we can figure out what URL corresponds to
        # WBS components.
        d = getPage(self.reactor, url + 'system_types')
        d.addCallback(self._listSystems_get, url)
        return d

    def _listSystems_get(self, blob, url):
        doc = xobj.parse(blob)
        wbsUrl = None
        for systemType in doc.system_types.system_type:
            if systemType.name == 'infrastructure-windows-build-node':
                wbsUrl = systemType.id
                break
        else:
            raise RuntimeError("Could not find "
                    "infrastructure-windows-build-node system type")

        # Now filter the set of infra systems to just WBS systems.
        d = getPage(self.reactor, url + 'infrastructure_systems')
        d.addCallback(self._listSystems_filter, wbsUrl)
        return d

    def _listSystems_filter(self, blob, wbsUrl):
        doc = xobj.parse(blob)
        hostnames = set()
        for system in doc.systems.system:
            # Ignore non-WBS systems
            if system.system_type.href != wbsUrl:
                continue
            # If there's only one network (usual case) xobj doesn't figure out
            # that it's a collection.
            if isinstance(system.networks.network, list):
                networks = system.networks.network
            else:
                networks = [system.networks.network]
            # Pick a network. Any network.
            for network in networks:
                if network.dns_name:
                    hostnames.add(network.dns_name)
                    break
        return hostnames

    def getBuildService(self):
        d = self.listSystems()
        def acquire(hostnames):
            if not hostnames:
                raise RuntimeError("No rPath Windows Build Service nodes are "
                        "present. Please check the 'Infrastructure' view "
                        "and try again.")
            # TODO: track how many jobs are on each host and use that to pick
            # the one with the fewest jobs active.
            hostname = random.choice(list(hostnames))
            return 'http://%s/api' % (hostname,)
        d.addCallback(acquire)
        return d


class StringProtocol(tw_proto.Protocol):
    """
    Collect HTTP response data in a string and fire a callback when the
    response is complete.
    """

    def __init__(self):
        self.data = ''
        self.deferred = tw_defer.Deferred()

    def dataReceived(self, data):
        self.data += data

    def connectionLost(self, reason):
        if reason.check(tw_web_client.ResponseDone):
            self.deferred.callback(self.data)
        else:
            self.deferred.errback(reason)


def getPage(reactor, url):
    client = tw_web_client.Agent(reactor)
    d = client.request('GET', url)
    def cb_deliver(result):
        if result.code != 200:
            raise RuntimeError("HTTP error %s: %s" % (result.code,
                result.phrase))
        proto = StringProtocol()
        result.deliverBody(proto)
        return proto.deferred
    d.addCallback(cb_deliver)
    return d


def start(dispatcher):
    coordinator = Coordinator(dispatcher.clock, 'localhost')
    dispatcher.wig_coordinator = coordinator
