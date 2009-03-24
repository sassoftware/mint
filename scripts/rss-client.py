#!/usr/bin/python

import getpass
from lxml import etree as ET
import optparse
import sys
import urllib
import urllib2

from conary.lib import digestlib

def main():
    op = optparse.OptionParser(usage = "%prog [options] xml-stream")
    op.add_option('-s', '--server', help = "rBuilder Server Name")
    op.add_option('-u', '--username', help = "rBuilder User Name")

    options, args = op.parse_args()
    if not options.server:
        op.error("Server name not specified")
    if len(args) != 1:
        op.error("XML file not specified")

    try:
        xmlStream = RestClient('', '', '').getStream(args[0])
    except StreamOpenError, e:
        op.error(str(e))
        return 1

    try:
        items = parseFeedStream(xmlStream)
    except ParseError, e:
        op.error(str(e))
        return 2

    # Connect
    if options.username:
        username = options.username
    else:
        username = getUsername()
    password = getPassword()

    cli = RestClient(options.server, username, password)
    cookie = cli.getCookie()
    if not cookie:
        print "Authentication failed"
        return 1

    cli.upload(items)

def getUsername():
    while 1:
        print "Username: ",
        username = sys.stdin.readline().strip()
        if username:
            return username

def getPassword():
    while 1:
        password = getpass.getpass("Password: ")
        if password:
            return password

class ParseError(Exception):
    pass

class StreamOpenError(Exception):
    pass

def parseFeedStream(xmlStream):
    try:
        xmlDoc = ET.parse(xmlStream)
    except ET.XMLSyntaxError, e:
        raise ParseError("Unable to parse XML file: %s" % str(e))
    xmlRoot = xmlDoc.getroot()
    if xmlRoot.tag != 'rss' or xmlRoot.get('version') != '2.0':
        raise ParseError("XML document is not an RSS 2.0 stream")
    channels = xmlRoot.getchildren()
    if not channels:
        raise ParseError("Channel element not found")
    channel = channels[0]
    items = (x for x in channel.iterchildren() if x.tag == 'item')
    return items

class RestClient(object):
    def __init__(self, server, username, password):
        self.server = server
        self.username = username
        self.password = password

        self.opener = urllib2.OpenerDirector()
        self.opener.add_handler(urllib2.HTTPSHandler())
        self.opener.add_handler(urllib2.HTTPHandler())

        self._cookie = None

    def getCookie(self):
        if self._cookie is not None:
            return self._cookie

        loginUrl = "https://%s/processLogin" % self.server
        data = urllib.urlencode([
            ('username', self.username),
            ('password', self.password),
            ('rememberMe', "1"),
            ('to', urllib.quote('http://%s/' % self.server)),
        ])
        req = urllib2.Request(loginUrl, data = data, headers = {})
        ret = self.opener.open(req)
        # Junk the response
        ret.read()
        cookie = ret.headers.get('set-cookie')
        if not cookie or not cookie.startswith('pysid'):
            return None
        self._cookie = cookie.split(';', 1)[0]
        return self._cookie

    def upload(self, items):
        url = "https://%s/api/notices/contexts/default" % self.server

        cookie = self.getCookie()
        if cookie is None:
            raise Exception("Authentication failed")
        headers = {'Content-Type' : 'application/xml',
                   'Cookie' : cookie, }

        # First, grab all the available notices (non-logged-in)
        req = urllib2.Request(url)
        ret = self.opener.open(req)
        if ret.code != 200:
            raise StreamOpenError("Unable to download existing notices")
        upstreamItems = list(parseFeedStream(ret))
        upstreamItems = dict((self._hashItem(x), x) for x in upstreamItems)

        for item in items:
            if self._hashItem(item, local = True) in upstreamItems:
                continue
            itemData = ET.tostring(item, encoding = "UTF-8", xml_declaration = False)
            req = urllib2.Request(url, headers = headers)
            ret = self.opener.open(req, data = itemData)
            print ret.code
            print ret.read()
            print

    def _hashItem(self, item, local = False):
        """
        Generate some kind of unique identifier for this item.
        If local is False, the unique ID is generated out of the guid nodes,
        otherwise we use guid-upstream nodes.
        """
        # Make a copy of the item first
        elem = ET.fromstring(ET.tostring(item))
        guids = elem.findall('guid')
        if not local:
            for guid in guids:
                elem.remove(guid)
            guids = elem.findall('guid-upstream')
        if guids:
            guids = [ x.text for x in guids ]
            return ''.join(sorted(guids))
        # No guid-upstream; hash the node
        return digestlib.sha1(ET.tostring(elem)).hexdigest()

    def getStream(self, streamName):
        if not streamName.startswith("http"):
            try:
                xmlStream = file(streamName)
            except IOError, e:
                raise StreamOpenError("Unable to open XML file: %s" % str(e))
            return xmlStream

        req = urllib2.Request(streamName)
        ret = self.opener.open(req)
        if ret.code != 200:
            raise StreamOpenError("Unable to open XML stream %s" % xmlStreamName)
        return ret

if __name__ == '__main__':
    sys.exit(main())
