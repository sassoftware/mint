#!/usr/bin/python

import getpass
from lxml import etree as ET
import optparse
import sys
import urllib
import urllib2

def main():
    op = optparse.OptionParser(usage = "%prog [options] xml-file")
    op.add_option('-s', '--server', help = "rBuilder Server Name")
    op.add_option('-u', '--username', help = "rBuilder User Name")

    options, args = op.parse_args()
    if not options.server:
        op.error("Server name not specified")
    if len(args) != 1:
        op.error("XML file not specified")

    try:
        xmlStream = file(args[0])
    except IOError, e:
        op.error("Unable to open XML file: %s" % str(e))
        return 2

    try:
        xmlDoc = ET.parse(xmlStream)
    except ET.XMLSyntaxError, e:
        op.error("Unable to parse XML file: %s" % str(e))
        return 3
    xmlRoot = xmlDoc.getroot()
    if xmlRoot.tag != 'rss' or xmlRoot.get('version') != '2.0':
        op.error("XML document is not an RSS 2.0 stream")
        return 4
    channels = xmlRoot.getchildren()
    if not channels:
        op.error("Channel element not found")
        return 5
    channel = channels[0]
    items = (x for x in channel.iterchildren() if x.tag == 'item')

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
        url = "https://%s/api/v1/notices/contexts/default" % self.server

        cookie = self.getCookie()
        if cookie is None:
            raise Exception("Authentication failed")
        headers = {'Content-Type' : 'application/xml',
                   'Cookie' : cookie, }

        for item in items:
            itemData = ET.tostring(item, encoding = "UTF-8", xml_declaration = False)
            req = urllib2.Request(url, headers = headers)
            ret = self.opener.open(req, data = itemData)
            print ret.code
            print ret.read()
            print

if __name__ == '__main__':
    sys.exit(main())
