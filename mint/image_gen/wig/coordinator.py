#
# Copyright (c) 2011 rPath, Inc.
#

import logging
import random
import socket
from twisted.internet import defer as tw_defer
from twisted.internet import protocol as tw_proto
from twisted.web import client as tw_web_client
from xobj import xobj

log = logging.getLogger(__name__)


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
        url = 'http://%s/api/v1/inventory/' % (self.hostname,)
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
            if system.system_type.id != wbsUrl:
                continue
            # If there's only one network (usual case) xobj doesn't figure out
            # that it's a collection.
            if isinstance(system.networks.network, list):
                networks = system.networks.network
            else:
                networks = [system.networks.network]
            # Pick a network. Prefer 'pinned' addresses, and within each object
            # prefer IP over DNS since DNS often lies.
            candidates = []
            for network in networks:
                if network.dns_name:
                    pinned = network.pinned.lower() == 'true'
                    candidates.append((
                        pinned, network.ip_address, network.dns_name))
            if candidates:
                pinned, ip_address, dns_name = sorted(candidates)[-1]
                if ip_address:
                    hostnames.add(ip_address)
                elif dns_name:
                    hostnames.add(dns_name)
        return hostnames

    def getBuildService(self):
        d = self.listSystems()
        def acquire(hostnames):
            # TODO: track how many jobs are on each host and use that to pick
            # the one with the fewest jobs active.
            hostnames = list(hostnames)
            random.shuffle(hostnames)
            # Test the hostnames to make sure they work
            for hostname in hostnames:
                try:
                    socket.getaddrinfo(hostname, 0, 0, socket.SOCK_STREAM)
                except socket.gaierror, err:
                    log.error("Skipping Windows Build Service %r because it "
                            "is not resolvable: %s", hostname, str(err))
                    pass
                else:
                    return 'http://%s/api' % (hostname,)
            raise RuntimeError("No rPath Windows Build Service nodes are "
                    "present. Please check the 'Infrastructure' view "
                    "and try again.")
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
