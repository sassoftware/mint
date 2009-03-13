#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import testsetup

import os
import time

import mint_rephelp
from restlib import client as restClient

class BaseRestTest(mint_rephelp.WebRepositoryHelper):

    def getRestClient(self, uri, username = 'foouser', password = 'foopass',
                      admin = False, **kwargs):
        # Launch a mint server
        defUser = username or 'foouser'
        defPass = password or 'foopass'
        if admin:
            client, userId = self.quickMintAdmin(defUser, defPass)
        else:
            client, userId = self.quickMintUser(defUser, defPass)
        page = self.webLogin(defUser, defPass)
        if username is not None:
            pysid = page.headers['Set-Cookie'].split(';', 1)[0]
            headers = { 'Cookie' : page.headers['Set-Cookie'] }
        else:
            headers = {}
            # Unauthenticated request
        baseUrl = "http://%s:%s/api" % (page.server, page.port)
        client = Client(baseUrl, headers)
        client.server = page.server
        client.port = page.port
        client.baseUrl = baseUrl
        client.username = username
        client.password = password

        # Hack. Do the macro expansion in the URI - so we call __init__ again
        uri = self.makeUri(client, uri)
        client.__init__(uri, headers)
        client.connect()
        return client

    def newConnection(self, client, uri):
        uri = self.makeUri(client, uri)
        client.__init__(uri, client.headers)
        client.connect()
        return client

    def makeUri(self, client, uri):
        if uri.startswith('http://') or uri.startswith('https://'):
            return uri
        replDict = dict(username = client.username, password =
            client.password, port = client.port, server = client.server)

        return ("%s/%s" % (client.baseUrl, uri)) % replDict

class Client(restClient.Client):
    pass


